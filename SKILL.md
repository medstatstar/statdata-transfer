---
name: statdata-transfer
cn_name: 统计数据格式转换器
description: "Read/convert 50+ statistical software formats, preserving variable/value labels and missing-value metadata for binary stats formats. Side effects (declared): runs environment checks (scripts/check_env.py); may optionally pip-install missing packages on request; can invoke the local R interpreter for .rda/.rds/.RData/.mtw/.rec files via a fallback that is DISABLED by default and must be opted in with allow_r_exec=True. 读入/转存 50+ 统计软件格式，对统计二进制格式完整保留变量标签/值标签/特殊缺失值等元数据。副作用声明：运行环境检查（scripts/check_env.py）；可应要求 pip 安装缺失包；处理 .rda/.rds/.RData/.mtw/.rec 文件时可调用本地 R 解释器，但该回退默认禁用，需 allow_r_exec=True 显式开启。"
triggers:
  - "statdata-transfer"
  - "统计数据格式转换"
  - "spss stata sas 格式"
  - ".sav .dta .sas7bdat 读入"
  - "sav转dta 格式转换"
  - "variable labels 变量标签"
  - "metadata-preserved conversion"
metadata:
  {
    "openclaw": { "emoji": "🛠️", "icon": "assets/icon.svg" },
    "authors": ["medstatstar", "phoe-zip"],
    "version": "2.0.0",
    "license": "MIT",
    "tags": ["data-conversion", "statistics", "spss", "stata", "sas", "clinical-trials", "metadata", "pandas", "bidirectional"],
    "homepage": "https://github.com/medstatstar/statdata-transfer",
  }
---

# statdata-transfer | Statistical Data Format Converter

> 致敬 Stat/Transfer — 业界格式转换标杆 | Honoring Stat/Transfer — the industry standard

## Core Capabilities | 核心能力

| Ability | Description | 能力 | 说明 |
|---------|-------------|------|------|
| Read | SPSS/Stata/SAS/R … full metadata; text/JSON/detect-only keep subset | 读入 | 统计二进制格式完整保留元数据；文本/JSON 保留子集；12 种专有格式探测降级 |
| Convert | Inter-convert most stats formats: SPSS↔Stata↔R↔SAS XPT↔… | 转存 | 多数统计格式可互转（部分受限于规范） |
| Embed | Labels embed in Parquet/Feather/HDF5/JSON via schema.metadata | 元数据嵌入 | 标签嵌入 Arrow schema.metadata |
| Warn | Auto-detect metadata loss per conversion path | 丢失警告 | 自动检测并报告元数据损失 |

## Supported Formats | 支持格式

*50+ formats, sorted alphabetically. 按字母排序。*

| Format 格式 | Extension 扩展名 | Meta Preserve 元数据保留 |
|------------|-----------------|------------------------|
| CDISC ODM | `.odm` | ⚠️ Clinical data only |
| dBASE / FoxPro | `.dbf` | ⚠️ Read+Write, uppercase names |
| EpiData | `.rec` | ⚠️ Via R |
| EpiInfo | `.prj` `.xml` | ✅ XML structure |
| Excel | `.xlsx` `.xls` `.xlsm` | ⚠️ Extra sheet for labels; merged-cell fill |
| EViews | `.wf1` `.wf2` | ⚠️ JSON structure |
| Feather | `.feather` `.arrow` | ✅ Via schema |
| FST | `.fst` | ✗ Detect-only (proprietary format) |
| GraphPad Prism | `.pzfx` `.pz` | ⚠️ Multi-table |
| Gretl | `.gdt` `.gdtb` | ✅ String-tables |
| HDF5 | `.h5` `.hdf5` | ⚠️ Hierarchy + attribute labels |
| HTML | `.html` | ⚠️ Tables only |
| jamovi | `.omv` | ✅ JSON analysis |
| JMP | `.jmp` | ⚠️ Multi-table |
| JSON | `.json` | ✅ stat-full-meta |
| MATLAB | `.mat` | ⚠️ v7.3+ via h5py fallback |
| Mathematica | `.wdx` | ⚠️ Best-effort XML |
| Minitab | `.mtw` `.mpj` | ⚠️ Via R |
| MS Access | `.mdb` `.accdb` | ⚠️ Multi-table; needs system driver |
| ODS | `.ods` | ⚠️ Data only |
| ORC | `.orc` | ✅ Via schema |
| Origin | `.opju` `.oggu` | ⚠️ Best-effort |
| Parquet | `.parquet` | ✅ Via schema; partitioned datasets |
| R | `.rda` `.rds` `.rdata` | ✅ pyreadr; R-interpreter fallback opt-in (allow_r_exec) |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | ✅ |
| SPSS | `.sav` `.zsav` `.por` | ✅ |
| Stata | `.dta` | ✅ |
| Weka ARFF | `.arff` | ✅ Nominal mapping |
| XML | `.xml` | ⚠️ Structure preserved |

> ✅=Full · ⚠️=Partial/conditional · ✗=Not preserved
> 
> 12 detect-only formats (SAS CPORT `.cpt`, Statistica `.sta`, OxMetrics `.in7`, SYSTAT `.sys`/`.syd`, Paradox `.db`/`.px`, LIMDEP `.lpw`, NCSS `.ncss`) give clear export guidance — see README.

## Return Structure | 返回结构

```python
{
    "dataframe": pd.DataFrame,
    "metadata": {
        "file_format": "spss_sav",
        "row_count": 100, "column_count": 10,
        "variable_labels": {"q1": "Question 1"},
        "value_labels": {"q1": {1: "Yes", 2: "No"}},
        # ... 全部元数据 | all metadata fields
    },
    "warnings": [],
    "column_report": {"q1": {"source_type": "int", "pandas_dtype": "int64"}},
}
```

## Quick Start | 快速开始

```bash
# Check environment | 检查环境
python scripts/check_env.py --install

# Run via WorkBuddy (bilingual, auto-detects your language)
> convert data.sav to .dta
> read data.sav and show metadata
> 把 data.sav 转成 .dta 并保留变量标签
```

> For complete code examples, see `references/usage_examples.py`.
> 完整代码示例见 `references/usage_examples.py`。

## Dependencies | 依赖

```yaml
requires:
  bins: [python3]
  packages:
    core: [pyreadstat>=1.3.5, pyreadr, pandas]
    extended: [openpyxl, xlrd, scipy, h5py, pyarrow, lxml, odfpy, tableauhyperapi, dbfread, dbf, pyodbc]
```

> Full list: `requirements.txt` | 完整列表见 `requirements.txt`

## Detailed Docs | 详细文档

- **English**: [`README.md`](./README.md) — format limits, strategies, encoding, extension guide
- **中文**: [`README_ZH.md`](./README_ZH.md) — 格式限制、读入策略、编码注意事项、扩展指南

## Security | 安全

- **R deserialization is sandboxed by default | R 反序列化默认隔离**: `.rda/.rds/.RData` files are read with the pure-Python `pyreadr` parser (no code execution). If `pyreadr` fails, the skill does **NOT** silently fall back to the real R interpreter — instead it raises a clear error. Loading untrusted objects via R's `readRDS()/load()` can execute embedded code, so the R-interpreter fallback is **disabled by default** and only runs when you explicitly pass `allow_r_exec=True` on a TRUSTED file.
- **R scripts are static templates | R 脚本为静态模板**: When the opt-in R path is used, all R scripts are fully static templates; user inputs are passed only as CLI args (`commandArgs(trailingOnly=TRUE)` via `jsonlite`) — **never concatenated into executable R code**. Random temp filenames; no fixed paths.
- **Optional install | 可选安装**: `python scripts/check_env.py --install` only runs on explicit request.
- **Permissions required | 所需权限**: Read the input file; write the output file to a path you specify. No network access unless you explicitly request package installation. No destructive writes — existing `.hyper` outputs are backed up to `.bak` before overwrite.
- **Scope | 范围**: Statistical data formats only. Text/JSON formats preserve metadata subset only — see «Format Limits» in README.

## License | 许可证

MIT-0. See [`LICENSE`](./LICENSE). | 详见 [`LICENSE`](./LICENSE)。
