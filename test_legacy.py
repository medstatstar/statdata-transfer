"""test_legacy.py - statdata-transfer v1.10 新增格式回归测试

覆盖：dBASE .dbf（读+写）、MS Access .mdb/.accdb（缺文件降级）、
Mathematica .wdx、Origin .opju/.oggu（best-effort）、
以及 SAS CPORT / Statistica / OxMetrics / SYSTAT / Paradox / LIMDEP / NCSS 占位降级。
"""
import os
import io
import zipfile
import tempfile

import pandas as pd
import pytest

from scripts import reader_core, writer
from scripts.reader_legacy import _read_dbf, _write_dbf, _read_wdx, _read_origin


def _sample_df():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["阿尔法", "贝塔", "伽马"],
        "score": [9.5, 8.0, 7.5],
        "flag": [True, False, True],
    })


def test_dbf_roundtrip_types_and_values():
    df = _sample_df()
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "t.dbf")
        warns = _write_dbf(df, p)
        assert os.path.exists(p)
        res = _read_dbf(p, "ts")
        back = res["dataframe"]
        assert back.shape == df.shape
        # dBASE 字段名大写化（格式限制），值保真（中文 / 浮点 / 整数）
        assert list(back.columns) == ["ID", "NAME", "SCORE", "FLAG"]
        assert list(back["NAME"]) == ["阿尔法", "贝塔", "伽马"]
        assert list(back["SCORE"]) == [9.5, 8.0, 7.5]
        assert res["metadata"]["file_format"] == "dbf"


def test_dbf_via_public_api():
    df = _sample_df()
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "pub.dbf")
        writer.write_stat_file(df, p)
        res = reader_core.read_stat_file(p)
        assert res["dataframe"].shape == df.shape
        assert res["metadata"]["file_format"] == "dbf"


def test_wdx_read_best_effort():
    xml = (
        '<?xml version="1.0"?>\n'
        '<wx version="1.0"><section>'
        '<variable name="id"><value>1</value><value>2</value><value>3</value></variable>'
        '<variable name="name"><value>a</value><value>b</value><value>c</value></variable>'
        "</section></wx>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "d.wdx")
        with open(p, "w", encoding="utf-8") as f:
            f.write(xml)
        res = _read_wdx(p, "ts")
        df = res["dataframe"]
        assert list(df.columns) == ["id", "name"]
        assert df.shape[0] == 3
        assert "wdx" in res["metadata"]["file_format"]


def test_origin_opju_read_best_effort():
    xml = (
        "<Worksheet><Data>"
        '<row><c>id</c><c>name</c></row>'
        '<row><c>1</c><c>a</c></row>'
        '<row><c>2</c><c>b</c></row>'
        "</Data></Worksheet>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "prj.opju")
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("worksheet.xml", xml)
        res = _read_origin(p, "ts")
        df = res["dataframe"]
        assert list(df.columns) == ["id", "name"]
        assert df.shape[0] == 2
        assert "origin" in res["metadata"]["file_format"]


def test_access_missing_file_friendly_error():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "nope.mdb")
        # reader_core 在分发前统一校验文件存在 -> FileNotFoundError；
        # 若存在但损坏/无驱动 -> _read_access 抛 RuntimeError（含"无法打开"）
        with pytest.raises((FileNotFoundError, RuntimeError)) as exc:
            reader_core.read_stat_file(p)
        assert "无法打开" in str(exc.value) or "文件不存在" in str(exc.value) or "Access" in str(exc.value)


@pytest.mark.parametrize("ext,software_hint", [
    (".cpt", "SAS CPORT"),
    (".sta", "Statistica"),
    (".in7", "OxMetrics"),
    (".sys", "SYSTAT"),
    (".syd", "SYSTAT"),
    (".db", "Paradox"),
    (".px", "Paradox"),
    (".lpw", "LIMDEP"),
    (".ncss", "NCSS"),
])
def test_legacy_placeholders_raise_clear(ext, software_hint):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "x" + ext)
        # 占位 handler 不读文件内容，仅识别扩展名给清晰导出指引
        with open(p, "w") as f:
            f.write("placeholder")
        with pytest.raises(RuntimeError) as exc:
            reader_core.read_stat_file(p)
        msg = str(exc.value)
        assert "暂不支持" in msg


if __name__ == "__main__":
    test_dbf_roundtrip_types_and_values()
    test_dbf_via_public_api()
    test_wdx_read_best_effort()
    test_origin_opju_read_best_effort()
    test_access_missing_file_friendly_error()
    test_legacy_placeholders_raise_clear(".cpt", "SAS CPORT")
    print("ALL_LEGACY_TESTS_PASSED")
