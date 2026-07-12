"""
test_hyper.py - end-to-end round-trip test for Tableau Hyper (.hyper) support.

Covers:
  * mixed column types (bool / int / float / text / naive datetime /
    tz-aware datetime / timedelta / category)
  * value fidelity after DataFrame -> .hyper -> DataFrame
  * statdata_meta side-table round-trip (variable_labels / value_labels /
    special_missing / measurement_levels)

Run:  C:/Tools/anaconda3/python.exe -m pytest test_hyper.py -q
"""
from __future__ import annotations

import os
import tempfile
import zipfile

import pandas as pd
import pytest

from scripts import reader_core
from scripts.reader_tableau import _read_hyper, _write_hyper


def _make_sample_df() -> pd.DataFrame:
    n = 6
    base = pd.Timestamp("2024-01-15 10:30:00")
    df = pd.DataFrame(
        {
            "id": pd.array([10, 20, 30, 40, 50, 60], dtype="int64"),
            "score": pd.array([1.5, 2.5, 3.5, 4.5, 5.5, 6.5], dtype="float64"),
            "is_active": pd.array([True, False, True, False, True, False], dtype="bool"),
            "name": pd.array(["alpha", "beta", "gamma", "delta", "eps", "zeta"], dtype="object"),
            "ts": pd.array([base + pd.Timedelta(hours=i) for i in range(n)], dtype="datetime64[ns]"),
            "tstz": pd.array(
                [base.tz_localize("UTC") + pd.Timedelta(hours=i) for i in range(n)],
                dtype="datetime64[ns, UTC]",
            ),
            "delta": pd.array([pd.Timedelta(days=i) for i in range(n)], dtype="timedelta64[ns]"),
            "category": pd.array(
                ["x", "y", "x", "y", "x", "y"], dtype="category"
            ),
        }
    )
    # one NULL in the text column to exercise nullability
    df.loc[2, "name"] = None
    return df


def _make_meta() -> dict:
    return {
        "variable_labels": {
            "id": "Patient ID",
            "score": "Test Score",
            "is_active": "Active Flag",
            "name": "Name",
            "ts": "Timestamp (naive)",
            "tstz": "Timestamp (tz)",
            "delta": "Duration",
            "category": "Category",
        },
        "value_labels": {"score": {"1": "Low", "2": "High"}},
        "special_missing": {},
        "measurement_levels": {"score": "ordinal"},
    }


def test_hyper_roundtrip_types_and_values():
    df = _make_sample_df()
    meta = _make_meta()

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.hyper")
        warns = _write_hyper(df, path, metadata=meta)
        assert os.path.exists(path), "write produced no .hyper file"
        assert any("statdata_meta" in w for w in warns), "expected label side-table warning"

        res = _read_hyper(path, "2026-07-04T08:25:00")
        df2 = res["dataframe"]

    # ---- shape & column order preserved ----
    assert list(df2.columns) == list(df.columns), "column order changed"
    assert df2.shape == df.shape, "row/col count changed"

    # ---- values per column ----
    assert df2["id"].tolist() == df["id"].tolist()
    assert df2["score"].tolist() == df["score"].tolist()
    assert df2["is_active"].tolist() == df["is_active"].tolist()
    assert df2["name"].tolist() == df["name"].tolist()
    # datetime naive compares equal regardless of dtype representation
    assert (df2["ts"].astype("datetime64[ns]") == df["ts"].astype("datetime64[ns]")).all()
    # timedelta
    assert (df2["delta"].astype("timedelta64[ns]") == df["delta"].astype("timedelta64[ns]")).all()
    # category becomes text
    assert df2["category"].tolist() == df["category"].astype(str).tolist()


def test_hyper_metadata_roundtrip():
    df = _make_sample_df()
    meta = _make_meta()

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "meta.hyper")
        _write_hyper(df, path, metadata=meta)
        res = _read_hyper(path, "2026-07-04T08:25:00")

    md = res["metadata"]
    assert md["variable_labels"] == meta["variable_labels"], "variable_labels lost"
    assert md["value_labels"] == meta["value_labels"], "value_labels lost"
    assert md.get("measurement_levels") == meta["measurement_levels"], "measurement_levels lost"
    # special_missing empty dict survived (read seeds empty dict)
    assert md.get("special_missing", {}) == {}, "special_missing round-trip mismatch"


def test_hyper_via_public_api():
    """Exercise the public reader_core.read_stat_file dispatch, not just the
    private helpers, to confirm end-to-end wiring."""
    df = _make_sample_df()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "pub.hyper")
        _write_hyper(df, path, metadata=_make_meta())
        res = reader_core.read_stat_file(path)
    assert res["dataframe"].shape == df.shape
    # public dispatch correctly routed to the tableau reader
    assert res["metadata"]["file_format"] == "tableau_hyper"
    assert res["metadata"]["row_count"] == df.shape[0]
    assert res["metadata"]["column_count"] == df.shape[1]


def test_twbx_unpack_read():
    """A .twbx is a zip containing a data-less .twb plus an embedded .hyper.
    Unpacking must read the embedded extract and recover data + labels."""
    df = _make_sample_df()
    with tempfile.TemporaryDirectory() as tmp:
        hyper_path = os.path.join(tmp, "data.hyper")
        _write_hyper(df, hyper_path, metadata=_make_meta())

        twbx_path = os.path.join(tmp, "book.twbx")
        with open(hyper_path, "rb") as f:
            hyper_bytes = f.read()
        with zipfile.ZipFile(twbx_path, "w") as z:
            z.writestr("book.twb", b"<workbook><datasource>ref</datasource></workbook>")
            # realistic layout: extracted data lives under Data/<source>/
            z.writestr("Data/MySource/data.hyper", hyper_bytes)

        res = reader_core.read_stat_file(twbx_path)
        df2 = res["dataframe"]

    assert df2.shape == df.shape, df2.shape
    assert list(df2.columns) == list(df.columns)
    assert df2["id"].tolist() == df["id"].tolist()
    assert res["metadata"]["file_format"] == "tableau_twbx"
    assert any("data.hyper" in e for e in res["metadata"]["embedded_extracts"])
    # embedded .hyper carries statdata_meta, so labels must survive the round-trip
    assert res["metadata"]["variable_labels"] == _make_meta()["variable_labels"]


def test_twbx_no_hyper_raises():
    """A .twbx with only a .twb (no embedded extract) cannot yield data."""
    with tempfile.TemporaryDirectory() as tmp:
        twbx_path = os.path.join(tmp, "empty.twbx")
        with zipfile.ZipFile(twbx_path, "w") as z:
            z.writestr("book.twb", b"<workbook/>")
        with pytest.raises(RuntimeError):
            reader_core.read_stat_file(twbx_path)


def test_twb_raises():
    """A bare .twb workbook has no embedded data -> helpful error, not silent fail."""
    with tempfile.TemporaryDirectory() as tmp:
        twb_path = os.path.join(tmp, "book.twb")
        with open(twb_path, "wb") as f:
            f.write(b"<workbook/>")
        with pytest.raises(RuntimeError):
            reader_core.read_stat_file(twb_path)


if __name__ == "__main__":
    test_hyper_roundtrip_types_and_values()
    test_hyper_metadata_roundtrip()
    test_hyper_via_public_api()
    test_twbx_unpack_read()
    test_twbx_no_hyper_raises()
    test_twb_raises()
    print("ALL_HYPER_TESTS_PASSED")
