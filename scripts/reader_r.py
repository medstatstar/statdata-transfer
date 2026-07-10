"""
reader_r.py - R 格式读入（.rda/.rds/.rdata），含 ASCII XDR 回退
自动从 stat_reader.py 拆分生成
"""

from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Any

import pandas as pd
import pyreadr

from .reader_core import (ColumnInfo, RMeta, StatFileResult, _bilingual, _calc_missing_pct, _get_source_type, _build_column_report, _build_metadata)

# ============================================================
# R 格式读入（.rda/.rds/.rdata），含 ASCII XDR 回退
# ============================================================

def _check_pyreadr_rda_error(filepath: str, exc: Exception):
    """检查是否为 ASCII XDR 格式错误，并提供 R 安装引导。"""
    err_msg = str(exc)
    is_rda_error = (
        'RDA2' in err_msg or 'ASCII' in err_msg
        or 'unrecognized object' in err_msg.lower()
        or 'Unable to convert string' in err_msg
        or isinstance(exc, UnicodeDecodeError)
        or (hasattr(exc, 'args') and any('RDA2' in str(a) for a in exc.args))
    )
    if not is_rda_error:
        return

    try:
        with open(filepath, 'rb') as f:
            header = f.read(10)
        if header[:4] == b'RDA2':
            header_fmt = 'ASCII XDR (RDA2 — 旧版 R 格式)'
        elif header[:4] == b'RDX2':
            header_fmt = 'Binary XDR (RDX2)'
        else:
            header_fmt = f'未知 ({header[:4]!r})'
    except Exception:
        header_fmt = '未知'

    raise RuntimeError(
        f"\n{'='*60}\n"
        f"无法读入 R 数据文件: {filepath}\n"
        f"文件内部格式: {header_fmt}\n"
        f"原始错误: {err_msg}\n\n"
        f"pyreadr 不支持旧版 ASCII XDR 格式（RDA2 文件头）。\n\n"
        f"解决方案：\n\n"
        f"【方法 1】安装 R 环境（推荐）\n"
        f"  1. 下载 R: https://cran.r-project.org/bin/windows/base/\n"
        f"  2. 安装时勾选 'Add R to PATH'\n"
        f"  3. 安装后重新运行即可\n\n"
        f"【方法 2】先用 R 自行转换为 RDS 格式\n"
        f"  在 R 中运行：\n"
        f"    load(\"{filepath}\")\n"
        f"    saveRDS(对象名, file=\"output.rds\", version=3)\n\n"
        f"  然后用 stat_reader.py 读入 output.rds\n\n"
        f"安装 R 后，运行: C:\\Tools\\anaconda3\\python.exe scripts/check_env.py\n"
        f"{'='*60}"
    )



def _check_r_available() -> str | None:
    """检查 R 脚本解释器是否可用。返回 Rscript 路径或 None。"""
    import shutil
    # Check PATH
    rscript = shutil.which("Rscript")
    if rscript:
        return rscript
    # Check common locations
    common_paths = [
        r"C:\Program Files\R\R-4.5.1\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.4.3\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.4.2\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.4.1\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.4.0\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.3.3\bin\x64\Rscript.exe",
        r"C:\Tools\R-4.5.1\bin\x64\Rscript.exe",
        r"C:\Tools\R-4.4.3\bin\x64\Rscript.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return None



def _read_r_via_rscript(filepath: str, format_type: str, object_name: str | None,
                        timestamp: str) -> StatFileResult:
    """通过 Rscript 调用 R 读入 RDA/RDS 文件，作为 pyreadr 失败的后备方案。

    工作流程：
    1. 调用 R 的 load() 或 readRDS() 读入数据
    2. R 执行 summary() 和结构探测，将结果输出到 stdout
    3. 提取 stat-full-meta / statdata_meta 嵌入元数据
    4. 对于数据框，R 执行 write.csv() 输出 CSV
    5. Python 端解析输出并构造 DataFrame

    为避免 RDS 回读编码问题，采用 'R 写 CSV/delim + Pandas 读入' 路径。
    """
    import json
    import subprocess
    import tempfile

    warnings_list = []

    rscript_path = _check_r_available()
    if not rscript_path:
        raise RuntimeError(_bilingual("R 环境未安装。请安装 R: https://cran.r-project.org/", "R environment not installed. Please install R: https://cran.r-project.org/"))

    filepath_r = filepath.replace("\\", "/")

    # 使用项目目录下的临时文件（比系统 TEMP 我更可控，路径也更简单）
    # R 输出 CSV 文件，Python 用 pandas 读回
    tmp_csv = os.path.join(os.path.dirname(__file__), '_tmp_r_output.csv')
    tmp_csv_r = tmp_csv.replace("\\", "/")

    # Extract embedded metadata + column-level attributes from R
    extract_meta_r = (
        "extract_meta <- function(obj) { "
        "  meta1 <- attr(obj, 'stat-full-meta'); "
        "  meta2 <- attr(obj, 'statdata_meta'); "
        "  if (!is.null(meta1)) { cat('STAT_FULL_META:', meta1, '\\n') }; "
        "  if (!is.null(meta2) && is.null(meta1)) { cat('STATDATA_META:', meta2, '\\n') }; "
        "  lab_attr <- attr(obj, 'label'); "
        "  if (!is.null(lab_attr)) { cat('OBJ_LABEL:', lab_attr, '\\n') }; "
        "  # Column-level labels, levels, format, units "
        "  if (is.data.frame(obj)) { "
        "    for (cn in names(obj)) { "
        "      x <- obj[[cn]]; "
        "      l <- attr(x, 'label'); lv <- attr(x, 'levels'); fmt <- attr(x, 'format'); un <- attr(x, 'units'); "
        "      if (!is.null(l)) cat(paste0('COL_LABEL:', cn, '=', l, '\\n')); "
        "      if (!is.null(lv)) cat(paste0('COL_LEVELS:', cn, '=', paste(lv, collapse=','), '\\n')); "
        "      if (!is.null(fmt)) cat(paste0('COL_FORMAT:', cn, '=', fmt, '\\n')); "
        "      if (!is.null(un)) cat(paste0('COL_UNITS:', cn, '=', un, '\\n')); "
        "    } "
        "  } "
        "}"
    )

    try:
        if format_type == "r_rds":
            r_cmd = (
                f"{extract_meta_r}"
                f"obj <- readRDS('{filepath_r}'); "
                f"extract_meta(obj); "
                f"if (!is.data.frame(obj)) {{ obj <- as.data.frame(obj); }}; "
                f"write.csv(obj, file='{tmp_csv_r}', row.names=TRUE, fileEncoding='UTF-8'); "
                f"cat('\\n__R_METADATA__\\n'); "
                f"cat(paste('DIM:', dim(obj)[1], dim(obj)[2], '\\n')); "
                f"cat('OBJS:', deparse(substitute(obj)), '\\n')"
            )
        else:
            if object_name:
                r_cmd = (
                    f"{extract_meta_r}"
                    f"e <- new.env(); "
                    f"load('{filepath_r}', envir=e); "
                    f"if ('{object_name}' %in% ls(e)) {{ "
                    f"  obj <- get('{object_name}', envir=e); "
                    f"}} else {{ "
                    f"  stop('Object {object_name} not found. Available: ', paste(ls(e), collapse=', ')); "
                    f"}}; "
                    f"extract_meta(obj); "
                    f"if (!is.data.frame(obj)) {{ obj <- as.data.frame(obj); }}; "
                    f"write.csv(obj, file='{tmp_csv_r}', row.names=TRUE, fileEncoding='UTF-8'); "
                    f"cat('\\n__R_METADATA__\\n'); "
                    f"cat(paste('DIM:', dim(obj)[1], dim(obj)[2], '\\n')); "
                    f"cat('OBJS:', paste('{object_name}', collapse=' '), '\\n')"
                )
            else:
                r_cmd = (
                    f"{extract_meta_r}"
                    f"e <- new.env(); "
                    f"load('{filepath_r}', envir=e); "
                    f"objs <- ls(e); "
                    f"data <- NULL; "
                    f"objname <- NA; "
                    f"for (o in objs) {{ "
                    f"  obj <- get(o, envir=e); "
                    f"  if (is.data.frame(obj)) {{ data <- obj; objname <- o; break; }} "
                    f"}}; "
                    f"if (is.null(data)) {{ "
                    f"  obj <- get(objs[1], envir=e); "
                    f"  if (is.function(obj) || is.environment(obj)) {{ "
                    f"    data <- tryCatch(as.data.frame(as.list(obj)), error=function(e) NULL); "
                    f"  }}; "
                    f"  if (is.null(data)) {{ data <- as.data.frame(obj); }}; "
                    f"  objname <- objs[1]; "
                    f"}}; "
                    f"extract_meta(data); "
                    f"write.csv(data, file='{tmp_csv_r}', row.names=TRUE, fileEncoding='UTF-8'); "
                    f"cat('\\n__R_METADATA__\\n'); "
                    f"cat(paste('DIM:', nrow(data), ncol(data), '\\n')); "
                    f"cat('OBJS:', objname, '\\n')"
                )

        result = subprocess.run(
            [rscript_path, "-e", r_cmd],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace',
        )

        if result.returncode != 0:
            raise RuntimeError(_bilingual(f"R 执行失败:\n{result.stderr[:1000]}", f"R execution failed:\n{result.stderr[:1000]}"))

        if not os.path.exists(tmp_csv):
            raise ValueError(_bilingual("R 未生成预期的输出文件", "R did not generate the expected output file"))

        df = pd.read_csv(tmp_csv, index_col=0, encoding='utf-8')
        df.index = df.index.rename(None)

        # Capture R object info from stdout
        r_object_name = object_name if object_name else 'unknown'
        embedded_meta = None
        obj_label = None
        col_labels_parsed = {}
        
        if '__R_METADATA__' in result.stdout:
            for line in result.stdout.split('\n'):
                if line.startswith('OBJS:'):
                    r_object_name = line.split(':', 1)[1].strip()
                elif line.startswith('STAT_FULL_META:'):
                    meta_str = line.split(':', 1)[1].strip()
                    try:
                        embedded_meta = json.loads(meta_str)
                    except json.JSONDecodeError:
                        pass
                elif line.startswith('STATDATA_META:'):
                    if embedded_meta is None:
                        meta_str = line.split(':', 1)[1].strip()
                        try:
                            embedded_meta = json.loads(meta_str)
                        except json.JSONDecodeError:
                            pass
                elif line.startswith('OBJ_LABEL:'):
                    obj_label = line.split(':', 1)[1].strip()
                elif line.startswith('COL_LABELS:'):
                    # Legacy combined format (v1.6 and earlier)
                    col_part = line.split(':', 1)[1].strip()
                    if col_part:
                        for pair in col_part.split('|'):
                            if '=' in pair:
                                k, v = pair.split('=', 1)
                                col_labels_parsed[k] = v
                elif line.startswith('COL_LABEL:'):
                    # New per-column format
                    rest = line[len('COL_LABEL:'):]
                    if '=' in rest:
                        k, v = rest.split('=', 1)
                        col_labels_parsed[k] = v

        r_objects_info = {r_object_name: 'DataFrame'}

    finally:
        for p in [tmp_csv]:
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

    warnings_list.append(_bilingual(f"通过 R （{os.path.basename(rscript_path)}）间接读入（CSV bridging）。原始格式: {format_type}", f"Indirect read via R ({os.path.basename(rscript_path)}) (CSV bridging). Original format: {format_type}"))

    # 尝试从嵌入元数据还原
    var_labels = {}
    val_labels = {}
    special_missing = {}
    disp_width = {}
    storage_width = {}
    measure = {}
    alignment = {}
    missing_ranges = {}
    missing_user = {}
    col_to_label = {}
    
    if embedded_meta:
        var_labels = embedded_meta.get('variable_labels', {})
        raw_vl = embedded_meta.get('value_labels', {})
        for vn, vm in raw_vl.items():
            if isinstance(vm, dict):
                val_labels[vn] = {k: v for k, v in vm.items()}
            else:
                val_labels[vn] = vm
        special_missing = embedded_meta.get('special_missing', {})
        disp_width = embedded_meta.get('variable_display_width', {})
        storage_width = embedded_meta.get('variable_storage_width', {})
        measure = embedded_meta.get('variable_measure', {})
        alignment = embedded_meta.get('variable_alignment', {})
        missing_ranges = embedded_meta.get('missing_ranges', {})
        missing_user = embedded_meta.get('missing_user_values', {})
        col_to_label = embedded_meta.get('column_names_to_labels', {})
        warnings_list.append(_bilingual("R 回退路径：从 stat-full-meta / statdata_meta 属性还原全部 17 字段元数据", "R fallback path: restored all 17 metadata fields from stat-full-meta / statdata_meta attributes"))
    elif col_labels_parsed:
        var_labels = col_labels_parsed
        warnings_list.append(_bilingual("R 回退路径：从 R 原生 attributes 提取列标签", "R fallback path: extracted column labels from R native attributes"))
    
    if obj_label:
        warnings_list.append(_bilingual(f"文件标签（OBJ_LABEL）已提取", f"File label (OBJ_LABEL) extracted"))

    r_metadata = {
        "r_objects_in_file": r_objects_info,
        "r_selected_object": r_object_name,
        "r_attributes": {
            "obj_label": obj_label,
            **({ "col_labels": col_labels_parsed } if col_labels_parsed else {}),
        },
    }

    column_report: dict[str, ColumnInfo] = {}
    for col in df.columns:
        has_vl = col in val_labels
        orig_label = var_labels.get(col)
        col_alignment = alignment.get(col)
        col_measure = measure.get(col)
        col_disp_width = disp_width.get(col)
        col_storage_width = storage_width.get(col)
        
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=orig_label,
            has_value_labels=has_vl,
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None,
            display_width=col_disp_width,
            storage_width=col_storage_width,
            measure_level=col_measure,
            alignment=col_alignment,
            original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    return {
        "dataframe": df,
        "metadata": RMeta(
            file_format="r", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels=var_labels, value_labels=val_labels, special_missing=special_missing,
            date_origin=None, file_encoding=None, file_label=obj_label,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label=col_to_label,
            missing_user_values=missing_user, missing_ranges=missing_ranges,
            variable_display_width=disp_width, variable_storage_width=storage_width,
            variable_measure=measure, variable_alignment=alignment,
            column_names_to_labels=col_to_label, mr_sets={}, table_name=None,
            r_metadata=r_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }



def _read_r(filepath, timestamp, *, format_type, object_name=None) -> StatFileResult:
    import pyreadr

    warnings_list = []
    # R format via pyreadr - metadata will be extracted separately via stat-full-meta

    try:
        if format_type == "r_rds":
            result_r = pyreadr.read_r(filepath)
            if not result_r:
                raise ValueError(_bilingual("RDS 文件为空或无法解析", "RDS file is empty or cannot be parsed"))
            key = list(result_r.keys())[0]
            obj = result_r[key]
            r_object_name = key
            r_objects_info = {key: type(obj).__name__}
            if not isinstance(obj, pd.DataFrame):
                df, conversion_warnings = _convert_r_object_to_dataframe(obj, key)
                warnings_list.extend(conversion_warnings)
            else:
                df = obj
        else:
            result_r = pyreadr.read_r(filepath)
            if not result_r:
                raise ValueError(_bilingual("RDA 文件为空或无法解析", "RDA file is empty or cannot be parsed"))

            r_objects_info = {}
            for k, v in result_r.items():
                r_objects_info[k] = type(v).__name__

            if object_name is not None:
                if object_name not in result_r:
                    raise ValueError(_bilingual(f"RDA 文件中不存在对象 '{object_name}'。可用对象: {list(result_r.keys())}", f"Object '{object_name}' not found in RDA file. Available: {list(result_r.keys())}"))
                obj = result_r[object_name]
                r_object_name = object_name
                if isinstance(obj, pd.DataFrame):
                    df = obj
                else:
                    df, conversion_warnings = _convert_r_object_to_dataframe(obj, object_name)
                    warnings_list.extend(conversion_warnings)
            elif len(result_r) == 1:
                key = list(result_r.keys())[0]
                obj = result_r[key]
                r_object_name = key
                if isinstance(obj, pd.DataFrame):
                    df = obj
                else:
                    df, conversion_warnings = _convert_r_object_to_dataframe(obj, key)
                    warnings_list.extend(conversion_warnings)
            else:
                dataframes_found = {k: v for k, v in result_r.items() if isinstance(v, pd.DataFrame)}
                if len(dataframes_found) == 1:
                    key = list(dataframes_found.keys())[0]
                    df = dataframes_found[key]
                    r_object_name = key
                else:
                    first_key = list(result_r.keys())[0]
                    first_obj = result_r[first_key]
                    df, conversion_warnings = _convert_r_object_to_dataframe(first_obj, first_key)
                    r_object_name = first_key
                    warnings_list.extend(conversion_warnings)
                    warnings_list.append(_bilingual(
                        f"RDA 文件包含多个对象 {list(result_r.keys())}，已尝试转换第一个对象 '{first_key}'。建议使用 object_name 指定对象，或使用 read_all_r_objects() 读入全部对象",
                        f"RDA file contains multiple objects {list(result_r.keys())}, attempted to convert first object '{first_key}'. Recommend using object_name to specify, or read_all_r_objects() to read all"
                    ))
    except pyreadr.custom_errors.LibrdataError as e:
        # 尝试自动回退到 R 脚本
        rscript_path = _check_r_available()
        if rscript_path:
            return _read_r_via_rscript(filepath, format_type, object_name, timestamp)
        else:
            _check_pyreadr_rda_error(filepath, e)
            raise
    except (ValueError, UnicodeDecodeError) as e:
        rscript_path = _check_r_available()
        if rscript_path:
            return _read_r_via_rscript(filepath, format_type, object_name, timestamp)
        raise

    # 提取 R 属性（含 stat-full-meta / statdata_meta 元数据）
    # pyreadr 不保留 R 对象属性，需用 R script 直接从 R 文件提取 statdata_meta
    r_attributes = _extract_r_attributes(df)
    embedded_meta_from_r = _extract_embedded_r_metadata(filepath, format_type, object_name)
    if embedded_meta_from_r:
        r_attributes['statdata_meta'] = embedded_meta_from_r
    
    # 尝试从嵌入的 stat-full-meta / statdata_meta 还原元数据
    embedded_meta = r_attributes.get('stat-full-meta') or r_attributes.get('statdata_meta')
    
    # 初始化元数据字段（默认空）
    var_labels = {}
    val_labels = {}
    special_missing = {}
    disp_width = {}
    storage_width = {}
    measure = {}
    alignment = {}
    missing_ranges = {}
    missing_user = {}
    col_to_label = {}
    
    if embedded_meta:
        if embedded_meta.get('variable_labels'):
            var_labels = embedded_meta['variable_labels']
        if embedded_meta.get('value_labels'):
            # 还原值标签中的数值键（JSON 序列化后变成字符串）
            val_labels = _parse_value_labels(embedded_meta['value_labels'])
        if embedded_meta.get('special_missing'):
            special_missing = embedded_meta['special_missing']
        if embedded_meta.get('variable_display_width'):
            disp_width = embedded_meta['variable_display_width']
        if embedded_meta.get('variable_storage_width'):
            storage_width = embedded_meta['variable_storage_width']
        if embedded_meta.get('variable_measure'):
            measure = embedded_meta['variable_measure']
        if embedded_meta.get('variable_alignment'):
            alignment = embedded_meta['variable_alignment']
        if embedded_meta.get('missing_ranges'):
            missing_ranges = embedded_meta['missing_ranges']
        if embedded_meta.get('missing_user_values'):
            missing_user = embedded_meta['missing_user_values']
        if embedded_meta.get('column_names_to_labels'):
            col_to_label = embedded_meta['column_names_to_labels']
        warnings_list.append(_bilingual("从 stat-full-meta 属性还原全部 17 字段元数据", "Restored all 17 metadata fields from stat-full-meta attribute"))
    
    # 同时从 R 原生 attributes 补充 column_labels（variable_labels）
    if not var_labels and 'column_labels' in r_attributes:
        var_labels = r_attributes['column_labels']
    
    r_metadata = {
        "r_objects_in_file": r_objects_info,
        "r_selected_object": r_object_name,
        "r_attributes": r_metadata_attrs if (r_metadata_attrs := {k: v for k, v in r_attributes.items() if k not in ('stat-full-meta', 'statdata_meta')}) else r_attributes,
    }
    
    # 如果有嵌入元数据，将 variable_labels 也放入 r_metadata 中供追溯
    if var_labels:
        r_metadata["variable_labels_restored"] = bool(var_labels)
    if val_labels:
        r_metadata["value_labels_restored"] = bool(val_labels)

    column_report: dict[str, ColumnInfo] = {}
    for col in df.columns:
        has_vl = col in val_labels
        orig_label = var_labels.get(col)
        col_alignment = alignment.get(col)
        col_measure = measure.get(col)
        col_disp_width = disp_width.get(col)
        col_storage_width = storage_width.get(col)
        
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=orig_label,
            has_value_labels=has_vl,
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None,
            display_width=col_disp_width,
            storage_width=col_storage_width,
            measure_level=col_measure,
            alignment=col_alignment,
            original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    return {
        "dataframe": df,
        "metadata": RMeta(
            file_format="r", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels=var_labels, value_labels=val_labels, special_missing=special_missing,
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label=col_to_label,
            missing_user_values=missing_user, missing_ranges=missing_ranges,
            variable_display_width=disp_width, variable_storage_width=storage_width,
            variable_measure=measure, variable_alignment=alignment,
            column_names_to_labels=col_to_label, mr_sets={}, table_name=None,
            r_metadata=r_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }



def _read_r_single(obj, object_name: str, timestamp: str) -> StatFileResult:
    """读入单个 R 对象并返回 StatFileResult。"""
    import pyreadr

    warnings_list = []
    df = None

    if isinstance(obj, pd.DataFrame):
        df = obj
    elif hasattr(obj, '__iter__') and not isinstance(obj, str):
        try:
            df = pd.DataFrame(obj)
            warnings_list.append(_bilingual(f"R 对象 '{object_name}' 类型为 {type(obj).__name__}，已尝试转换为 DataFrame", f"R object '{object_name}' of type {type(obj).__name__}, attempted conversion to DataFrame"))
        except Exception as e:
            raise ValueError(f"R 对象 '{object_name}' 类型为 {type(obj).__name__}，无法转换为 DataFrame: {str(e)[:200]}")
    else:
        raise ValueError(f"R 对象 '{object_name}' 类型为 {type(obj).__name__}，无法转换为 DataFrame")

    r_attributes = _extract_r_attributes(df)

    column_report: dict[str, ColumnInfo] = {}
    for col in df.columns:
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=None,
            has_value_labels=False,
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None,
            display_width=None,
            storage_width=None,
            measure_level=None,
            alignment=None,
            original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    return {
        "dataframe": df,
        "metadata": RMeta(
            file_format="r", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels={}, value_labels={}, special_missing={},
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label={},
            missing_user_values={}, missing_ranges={},
            variable_display_width={}, variable_storage_width={},
            variable_measure={}, variable_alignment={},
            column_names_to_labels={}, mr_sets={}, table_name=None,
            r_metadata={
                "r_objects_in_file": {object_name: type(obj).__name__},
                "r_selected_object": object_name,
                "r_attributes": r_attributes,
            },
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_r_attributes(obj: Any) -> dict[str, Any]:
    """从 R 对象提取 attributes，包括 stat-full-meta 元数据。"""
    import json
    
    attributes = {}
    
    # 1. 提取 stat-full-meta（v1.6+ 嵌入的统一元数据）
    stat_full_meta = None
    if hasattr(obj, 'attrs') and 'stat-full-meta' in obj.attrs:
        try:
            meta_json = obj.attrs['stat-full-meta']
            if isinstance(meta_json, str):
                stat_full_meta = json.loads(meta_json)
            elif isinstance(meta_json, bytes):
                stat_full_meta = json.loads(meta_json.decode('utf-8'))
            attributes['stat-full-meta'] = stat_full_meta
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            attributes['stat-full-meta-error'] = str(e)
    
    # 2. 提取旧版 statdata_meta（v1.5-）
    if stat_full_meta is None and hasattr(obj, 'attrs') and 'statdata_meta' in obj.attrs:
        try:
            meta_json = obj.attrs['statdata_meta']
            if isinstance(meta_json, str):
                stat_full_meta = json.loads(meta_json)
            elif isinstance(meta_json, bytes):
                stat_full_meta = json.loads(meta_json.decode('utf-8'))
            attributes['statdata_meta'] = stat_full_meta
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            attributes['statdata_meta-error'] = str(e)
    
    # 3. 提取 R 原生属性：label, labels, units, format, class, names
    if hasattr(obj, 'attrs'):
        for k in ['label', 'labels', 'units', 'format', 'class', 'names', 'row.names', 'comment']:
            if k in obj.attrs:
                v = obj.attrs[k]
                if isinstance(v, str) and len(v) > 500:
                    v = v[:500] + '...[truncated]'
                attributes[k] = str(v) if not isinstance(v, str) else v
    
    # Extract column-level attributes (variable_labels, value_labels, levels, format, etc.)
    if hasattr(obj, 'columns'):
        col_labels = {}
        col_units = {}
        col_levels = {}
        col_formats = {}
        for col in obj.columns:
            if hasattr(obj[col], 'attrs'):
                col_attrs = obj[col].attrs
                if 'label' in col_attrs:
                    col_labels[col] = str(col_attrs['label'])
                elif 'labels' in col_attrs:
                    # R 的 labels 属性通常对应 value labels
                    labels_val = col_attrs['labels']
                    if hasattr(labels_val, 'tolist'):
                        col_labels[col] = str(labels_val.tolist())
                    else:
                        col_labels[col] = str(labels_val)
                if 'units' in col_attrs:
                    col_units[col] = str(col_attrs['units'])
                if 'levels' in col_attrs:
                    lv = col_attrs['levels']
                    if hasattr(lv, 'tolist'):
                        col_levels[col] = [str(x) for x in lv.tolist()]
                    else:
                        col_levels[col] = str(lv)
                if 'format' in col_attrs:
                    col_formats[col] = str(col_attrs['format'])
        if col_labels:
            attributes['column_labels'] = col_labels
        if col_units:
            attributes['column_units'] = col_units
        if col_levels:
            attributes['column_levels'] = col_levels
        if col_formats:
            attributes['column_formats'] = col_formats
    
    if hasattr(obj, 'index') and hasattr(obj.index, 'name'):
        if obj.index.name is not None:
            attributes['index_name'] = str(obj.index.name)
    
    return attributes


def _extract_embedded_r_metadata(filepath: str, format_type: str, object_name: str | None) -> dict:
    """通过 R script 直接从 R 文件提取 statdata_meta 属性（pyreadr 不保留 R 属性）"""
    try:
        rscript_path = _check_r_available()
        if not rscript_path:
            return {}
        
        filepath_r = filepath.replace("\\", "/")
        
        if format_type == "r_rds":
            r_cmd = (
                f"obj <- readRDS('{filepath_r}'); "
                f"meta <- attr(obj, 'statdata_meta'); "
                f"if (is.null(meta)) {{ cat('__NOMETA__\\n') }} else {{ cat(meta) }}"
            )
        else:
            if object_name:
                r_cmd = (
                    f"e <- new.env(); "
                    f"load('{filepath_r}', envir=e); "
                    f"obj <- get('{object_name}', envir=e); "
                    f"meta <- attr(obj, 'statdata_meta'); "
                    f"if (is.null(meta)) {{ cat('__NOMETA__\\n') }} else {{ cat(meta) }}"
                )
            else:
                r_cmd = (
                    f"e <- new.env(); "
                    f"load('{filepath_r}', envir=e); "
                    f"objs <- ls(e); "
                    f"data <- NULL; "
                    f"for (o in objs) {{ "
                    f"  obj <- get(o, envir=e); "
                    f"  if (is.data.frame(obj)) {{ data <- obj; break; }} "
                    f"}}; "
                    f"if (is.null(data)) {{ obj <- get(objs[1], envir=e); }}; "
                    f"meta <- attr(data, 'statdata_meta'); "
                    f"if (is.null(meta)) {{ cat('__NOMETA__\\n') }} else {{ cat(meta) }}"
                )
        
        result = subprocess.run(
            [rscript_path, "-e", r_cmd],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace',
        )
        
        if result.returncode != 0 or '__NOMETA__' in result.stdout:
            return {}
        
        # Parse the JSON from stdout (it should be the only output on success)
        output = result.stdout.strip()
        if not output or output == '__NOMETA__':
            return {}
        
        return json.loads(output)
    except Exception:
        return {}


def read_all_r_objects_inner(filepath: str) -> dict[str, StatFileResult]:
    """Read all R objects from a .rda file. Returns {object_name: StatFileResult}."""
    import pyreadr
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        result_r = pyreadr.read_r(filepath)
    except Exception as e:
        rscript_path = _check_r_available()
        if rscript_path:
            return _read_all_r_objects_via_rscript(filepath, rscript_path)
        raise RuntimeError(f"Cannot read R file and R is not available: {e}")
    
    timestamp = datetime.now().isoformat(timespec="seconds")
    results = {}
    
    for obj_name, obj in result_r.items():
        if isinstance(obj, pd.DataFrame):
            results[obj_name] = _read_r_single(obj, obj_name, timestamp)
    
    if not results:
        raise ValueError(f"No DataFrames found in R file. Objects: {list(result_r.keys())}")
    
    return results


def _read_all_r_objects_via_rscript(filepath: str, rscript_path: str) -> dict[str, StatFileResult]:
    """Fallback: list all data frames in RDA via R, then extract each."""
    filepath_r = filepath.replace("\\", "/")
    r_cmd = (
        f"e <- new.env(); "
        f"load('{filepath_r}', envir=e); "
        f"objs <- ls(e); "
        f"for (o in objs) {{ "
        f"  obj <- get(o, envir=e); "
        f"  if (is.data.frame(obj)) {{ cat('DF:', o, '\\n') }} "
        f"}}"
    )
    
    res = subprocess.run(
        [rscript_path, "-e", r_cmd],
        capture_output=True, text=True, timeout=60,
        encoding="utf-8", errors="replace",
    )
    
    df_names = []
    for line in res.stdout.split("\n"):
        if line.startswith("DF:"):
            df_names.append(line.split(":", 1)[1].strip())
    
    if not df_names:
        raise ValueError("No DataFrames found via Rscript")
    
    # Use load() approach for each - we'll read the full file and use pyreadr again
    # or use the _read_r_single approach
    import pyreadr
    result_r = pyreadr.read_r(filepath)
    timestamp = datetime.now().isoformat(timespec="seconds")
    results = {}
    for name in df_names:
        if name in result_r and isinstance(result_r[name], pd.DataFrame):
            results[name] = _read_r_single(result_r[name], name, timestamp)
    
    return results


def _convert_r_object_to_dataframe(obj, obj_name):
    """尝试将 R 对象转换为 DataFrame"""
    warnings_list = []
    if isinstance(obj, pd.DataFrame):
        return obj, warnings_list
    if hasattr(obj, '__iter__') and not isinstance(obj, str):
        try:
            df = pd.DataFrame(obj)
            warnings_list.append(_bilingual(f"R 对象 '{obj_name}' 类型为 {type(obj).__name__}，已尝试转换为 DataFrame", f"R object '{obj_name}' of type {type(obj).__name__}, attempted conversion to DataFrame"))
            return df, warnings_list
        except Exception as e:
            raise ValueError(_bilingual(f"R 对象 '{obj_name}' 类型为 {type(obj).__name__}，无法转换为 DataFrame: {str(e)[:200]}", f"R object '{obj_name}' of type {type(obj).__name__}, cannot be converted to DataFrame: {str(e)[:200]}"))
    else:
        raise ValueError(_bilingual(f"R 对象 '{obj_name}' 类型为 {type(obj).__name__}，无法转换为 DataFrame", f"R object '{obj_name}' of type {type(obj).__name__}, cannot be converted to DataFrame"))


