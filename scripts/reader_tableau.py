"""
reader_tableau.py - Tableau Hyper (.hyper) read/write bridge.

Reads a Tableau Hyper extract file into a pandas DataFrame, recovering
``statdata_meta`` (variable labels / value labels / special missing) from a
side-table when present. Writes a DataFrame to a ``.hyper`` file using the
official Tableau Hyper API.

Security notes
--------------
* Uses the official ``tableauhyperapi`` package (Tableau/Salesforce, Apache-2.0).
* No shell, no R subprocess, no string interpolation into executable code.
* All table/column identifiers are passed through the typed Hyper API; the
  only string we interpolate is JSON metadata we ourselves generated.
"""
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from typing import Any

import pandas as pd
from tableauhyperapi import (
    Connection,
    CreateMode,
    HyperProcess,
    Inserter,
    Interval as HyperInterval,
    Nullability,
    SchemaName,
    SqlType,
    TableDefinition,
    TableName,
    Telemetry,
)

from .reader_core import (
    StatFileResult,
    _build_column_report,
    _build_metadata,
    _calc_missing_pct,
    _bilingual,
)

HYPER_TELEMETRY = Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU
SYS_SCHEMAS = {"pg_catalog", "information_schema"}
EXTRACT_SCHEMA = "Extract"
EXTRACT_TABLE = "Extract"
META_SCHEMA = "statdata"
META_TABLE = "meta"

# keys we persist into the statdata_meta side-table
_META_KEYS = ("variable_labels", "value_labels", "special_missing", "measurement_levels")


def _unquote(name: Any) -> str:
    # TableName/column identifiers render as "Schema"."Table" (quoted).
    # Strip every quote so we can match against plain names like Extract.Extract.
    return str(name).replace('"', '')


# ============================================================
# READ
# ============================================================
def _read_hyper(filepath: str, timestamp: str) -> StatFileResult:
    """Read a Tableau ``.hyper`` file into a StatFileResult dict."""
    warnings_list: list[str] = []

    hyper = HyperProcess(telemetry=HYPER_TELEMETRY)
    conn = Connection(
        endpoint=hyper.endpoint,
        database=filepath,
        create_mode=CreateMode.NONE,
    )
    try:
        # enumerate user tables (skip system schemas)
        schemas = conn.catalog.get_schema_names()
        tables: list[TableName] = []
        for s in schemas:
            if _unquote(s) in SYS_SCHEMAS:
                continue
            for t in conn.catalog.get_table_names(s):
                tables.append(t)

        if not tables:
            raise RuntimeError(_bilingual(
                f"Hyper 文件中未找到任何数据表: {filepath}",
                f"No data table found in Hyper file: {filepath}",
            ))

        # prefer the Tableau extract convention "Extract"."Extract"
        target = None
        for t in tables:
            if _unquote(t) == f"{EXTRACT_SCHEMA}.{EXTRACT_TABLE}":
                target = t
                break
        if target is None:
            target = tables[0]

        query = "SELECT * FROM %s" % str(target)
        result = conn.execute_query(query)
        col_defs = [(c.name.unescaped, str(c.type).lower()) for c in result.schema.columns]
        columns = [n for n, _ in col_defs]

        # convert Hyper-native types to pandas-friendly Python types while reading,
        # so DataFrame construction succeeds (pandas cannot ingest Timestamp/Interval directly)
        def _coerce(v, sqltype):
            if "interval" in sqltype:
                if isinstance(v, HyperInterval):
                    return pd.Timedelta(days=v.days, microseconds=v.microseconds)
                return v
            if "timestamp" in sqltype:
                if hasattr(v, "to_datetime"):
                    return v.to_datetime()
                return v
            return v

        rows = []
        while result.next_row():
            vals = result.get_values()
            rows.append(
                tuple(_coerce(v, sqltype) for v, (_, sqltype) in zip(vals, col_defs))
            )
        df = pd.DataFrame(rows, columns=columns)
        result.close()

        # recover statdata_meta side-table if present
        all_meta: dict[str, Any] = {
            "variable_labels": {},
            "value_labels": {},
            "special_missing": {},
        }
        if conn.catalog.has_table(TableName(META_SCHEMA, META_TABLE)):
            try:
                mres = conn.execute_query(
                    'SELECT "json" FROM "%s"."%s"' % (META_SCHEMA, META_TABLE)
                )
                try:
                    if mres.next_row():
                        stored = json.loads(mres.get_value(0))
                        if isinstance(stored, dict):
                            for k in _META_KEYS:
                                if k in stored and isinstance(stored[k], dict):
                                    all_meta[k] = stored[k]
                finally:
                    mres.close()
            except Exception:
                # never fail the whole read because of a malformed meta side-table
                pass

        column_report = _build_column_report(
            df,
            all_meta,
            all_meta.get("value_labels", {}),
            {},
            {},
            warnings_list,
            "tableau_hyper",
        )

        metadata = _build_metadata(
            all_meta,
            "tableau_hyper",
            {
                "collected_at": timestamp,
                "row_count": df.shape[0],
                "column_count": df.shape[1],
                "total_missing_pct": _calc_missing_pct(df),
            },
        )
    finally:
        conn.close()
        hyper.close()

    return {
        "dataframe": df,
        "metadata": metadata,
        "warnings": warnings_list,
        "column_report": column_report,
    }


# ============================================================
# READ - Tableau packaged workbook (.twbx)
# ============================================================
def _read_twbx(filepath: str, timestamp: str) -> StatFileResult:
    """Read a Tableau packaged workbook (.twbx).

    A .twbx is a zip archive containing a .twb workbook (XML definition, no
    data) plus one or more embedded data extracts — usually ``.hyper`` files.
    We unpack the embedded ``.hyper`` extract(s) to a temp dir and delegate to
    :func:`_read_hyper`, returning the first extract's data (the rest are
    listed in warnings). Legacy ``.tde`` extracts are detected but not read.
    """
    warnings_list: list[str] = []
    with zipfile.ZipFile(filepath) as z:
        names = z.namelist()
    hyper_entries = [n for n in names if n.lower().endswith(".hyper")]
    tde_entries = [n for n in names if n.lower().endswith(".tde")]

    if not hyper_entries:
        raise RuntimeError(
            _bilingual(
                ".twbx 内未找到任何 .hyper 数据提取，无法读取数据表（.twb 工作簿本身不含数据；"
                "若为旧版 .tde 提取暂不支持）",
                "No .hyper extract found inside .twbx; cannot read a data table "
                "(the .twb workbook holds no data; legacy .tde is not yet supported)",
            )
        )

    results = []
    with zipfile.ZipFile(filepath) as z, tempfile.TemporaryDirectory() as tmp:
        for i, h in enumerate(hyper_entries):
            dest = os.path.join(tmp, "embedded_%d.hyper" % i)
            with z.open(h) as src, open(dest, "wb") as out:
                out.write(src.read())
            results.append((h, _read_hyper(dest, timestamp)))

    primary_name, primary = results[0]
    primary["metadata"]["file_format"] = "tableau_twbx"
    primary["metadata"]["source_container"] = "tableau_twbx"
    primary["metadata"]["embedded_extracts"] = hyper_entries
    primary["warnings"].append(
        _bilingual(
            "已从 .twbx 解包并读取内嵌 .hyper 数据提取: %s" % ", ".join(hyper_entries),
            "Unpacked and read embedded .hyper extract(s) from .twbx: %s"
            % ", ".join(hyper_entries),
        )
    )
    if len(results) > 1:
        primary["warnings"].append(
            _bilingual(
                "检测到 %d 个内嵌数据提取，仅返回首个「%s」；其余未读取: %s"
                % (len(results), primary_name, ", ".join(n for n, _ in results[1:])),
                "Found %d embedded extracts; only the first «%s» is returned; others "
                "not read: %s" % (len(results), primary_name, ", ".join(n for n, _ in results[1:])),
            )
        )
    if tde_entries:
        primary["warnings"].append(
            _bilingual(
                "发现 %d 个旧版 .tde 提取未读取（暂不支持）: %s"
                % (len(tde_entries), ", ".join(tde_entries)),
                "Found %d legacy .tde extract(s) not read (unsupported yet): %s"
                % (len(tde_entries), ", ".join(tde_entries)),
            )
        )
    return primary


def _read_twb(filepath: str, timestamp: str) -> StatFileResult:
    """A bare .twb workbook holds no embedded data — refuse with guidance."""
    raise RuntimeError(
        _bilingual(
            ".twb 是 Tableau 工作簿（XML 定义），本身不含数据表，无法作为数据文件读取；"
            "请使用打包工作簿 .twbx（含内嵌 .hyper）或直接提供 .hyper 提取文件",
            ".twb is a Tableau workbook (XML definition) with no embedded data; cannot be "
            "read as a data file. Use a packaged .twbx (embeds .hyper) or a .hyper extract directly",
        )
    )


# ============================================================
# WRITE
# ============================================================
def _pandas_col_to_hyper(series: pd.Series):
    """Map a pandas Series dtype to a (SqlType, nullable) pair."""
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype):
        return SqlType.bool(), True
    if pd.api.types.is_integer_dtype(dtype):
        return SqlType.big_int(), True
    if pd.api.types.is_float_dtype(dtype):
        return SqlType.double(), True
    if pd.api.types.is_datetime64_any_dtype(dtype):
        if getattr(dtype, "tz", None) is not None:
            return SqlType.timestamp_tz(), True
        return SqlType.timestamp(), True
    if pd.api.types.is_timedelta64_dtype(dtype):
        return SqlType.interval(), True
    # object / category / unknown -> text (values coerced to str)
    return SqlType.text(), True


def _convert_value(v: Any, series: pd.Series) -> Any:
    """Coerce a pandas cell value into a Hyper-acceptable Python type."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype):
        return bool(v)
    if pd.api.types.is_integer_dtype(dtype):
        return int(v)
    if pd.api.types.is_float_dtype(dtype):
        return float(v)
    if pd.api.types.is_datetime64_any_dtype(dtype):
        if hasattr(v, "to_pydatetime"):
            return v.to_pydatetime()
        return v
    if pd.api.types.is_timedelta64_dtype(dtype):
        # pandas Timedelta -> Hyper Interval (months always 0 for timedelta)
        days = v.days
        micros = v.seconds * 1_000_000 + v.microseconds
        return HyperInterval(months=0, days=days, microseconds=micros)
    # text column: str-coerce everything (Hyper TEXT is UTF-8)
    if v is None:
        return None
    return str(v)


def _write_meta_side_table(conn, metadata: dict) -> None:
    """Store statdata_meta as a single-row JSON side-table (best-effort)."""
    payload = {k: metadata[k] for k in _META_KEYS if metadata.get(k)}
    if not payload:
        return
    conn.catalog.create_schema_if_not_exists(SchemaName(META_SCHEMA))
    mt = TableDefinition(
        TableName(META_SCHEMA, META_TABLE),
        [TableDefinition.Column("json", SqlType.text(), Nullability.NOT_NULLABLE)],
    )
    conn.catalog.create_table_if_not_exists(mt)
    with Inserter(conn, mt) as mins:
        mins.add_row((json.dumps(payload, ensure_ascii=False),))
        mins.execute()


def _write_hyper(df: pd.DataFrame, filepath: str, metadata: dict | None = None, **kwargs) -> list:
    """Write a DataFrame to a Tableau ``.hyper`` file.

    Returns a list of metadata-loss warnings (mirrors the other writers).
    """
    warnings_list: list[str] = []
    metadata = metadata or {}

    if os.path.exists(filepath):
        os.remove(filepath)

    hyper = HyperProcess(telemetry=HYPER_TELEMETRY)
    conn = Connection(
        endpoint=hyper.endpoint,
        database=filepath,
        create_mode=CreateMode.CREATE_AND_REPLACE,
    )
    try:
        conn.catalog.create_schema(SchemaName(EXTRACT_SCHEMA))
        cols = []
        for col in df.columns:
            sql_type, nullable = _pandas_col_to_hyper(df[col])
            cols.append(
                TableDefinition.Column(
                    str(col),
                    sql_type,
                    Nullability.NULLABLE if nullable else Nullability.NOT_NULLABLE,
                )
            )
        td = TableDefinition(TableName(EXTRACT_SCHEMA, EXTRACT_TABLE), cols)
        conn.catalog.create_table(td)
        with Inserter(conn, td) as ins:
            for _, row in df.iterrows():
                ins.add_row(
                    tuple(_convert_value(v, df[col]) for col, v in row.items())
                )
            # commit the buffered rows (execute() flushes + closes the inserter)
            ins.execute()

        # persist statdata_meta for round-trip label recovery
        _write_meta_side_table(conn, metadata)

        # metadata-loss note (mirrors non-stat targets)
        if metadata.get("variable_labels") or metadata.get("value_labels"):
            warnings_list.append(
                _bilingual(
                    "变量/值标签通过 statdata_meta 副表存入 .hyper，仅本技能可读回；"
                    "Tableau 等外部工具打开时仅见数据列",
                    "Variable/value labels stored in a statdata_meta side-table, "
                    "readable only by this skill; Tableau sees data columns only",
                )
            )
    finally:
        conn.close()
        hyper.close()

    return warnings_list
