---
name: statdata-transfer
cn_name: 统计数据格式转换器
description: "读入/转存 50+ 统计软件格式，对统计二进制格式完整保留变量标签/值标签/特殊缺失值等元数据。副作用声明：运行环境检查（scripts/check_env.py）；可应要求 pip 安装缺失包；处理 .rda/.rds/.RData/.mtw/.rec 文件时可调用本地 R 解释器，但该回退默认禁用，需 allow_r_exec=True 显式开启。 / Read/convert 50+ statistical software formats, preserving variable/value labels and missing-value metadata for binary stats formats. Side effects (declared): runs environment checks (scripts/check_env.py); may optionally pip-install missing packages on request; can invoke the local R interpreter for .rda/.rds/.RData/.mtw/.rec files via a fallback that is DISABLED by default and must be opted in with allow_r_exec=True."
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
    "version": "2.1.0",
    "license": "MIT",
    "tags": ["data-conversion", "statistics", "spss", "stata", "sas", "clinical-trials", "metadata", "pandas", "bidirectional"],
    "homepage": "https://github.com/medstatstar/statdata-transfer",
  }
---

# statdata-transfer / Statistical Data Format Converter

> 致敬 Stat/Transfer — 业界格式转换标杆 / Honoring Stat/Transfer — the industry standard

## Language Policy / 语言策略

 - 默认英文；检测到中文环境时切换为中文提示。
 - 常用模块备英文 + 中文两套；文档标题（不区分语言者）采用「英 / 中」顺序双语。
 - 复杂 / 少用模块可暂只英文。

## Core Capabilities / 核心能力

| Ability / 能力 | Description / 说明 |
|---------|-------------|
| Read / 读入 | SPSS/Stata/SAS/R … full metadata; text/JSON/detect-only keep subset / 统计二进制格式完整保留元数据；文本/JSON 保留子集；12 种专有格式探测降级 |
| Convert / 转存 | Inter-convert most stats formats: SPSS↔Stata↔R↔SAS XPT↔… / 多数统计格式可互转（部分受限于规范） |
| Embed / 元数据嵌入 | Labels embed in Parquet/Feather/HDF5/JSON via schema.metadata / 标签嵌入 Arrow schema.metadata |
| Warn / 丢失警告 | Auto-detect metadata loss per conversion path / 自动检测并报告元数据损失 |

## Supported Formats / 支持格式

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

## Return Structure / 返回结构

```python
{
    "dataframe": pd.DataFrame,
    "metadata": {
        "file_format": "spss_sav",
        "row_count": 100, "column_count": 10,
        "variable_labels": {"q1": "Question 1"},
        "value_labels": {"q1": {1: "Yes", 2: "No"}},
        # ... 全部元数据 / all metadata fields
    },
    "warnings": [],
    "column_report": {"q1": {"source_type": "int", "pandas_dtype": "int64"}},
}
```

## Quick Start / 快速开始

```bash
# Check environment / 检查环境
python scripts/check_env.py --install

# Run via WorkBuddy (bilingual, auto-detects your language)
> convert data.sav to .dta
> read data.sav and show metadata
> 把 data.sav 转成 .dta 并保留变量标签
```

> For complete code examples, see `references/usage_examples.py`.
> 完整代码示例见 `references/usage_examples.py`。

## Dependencies / 依赖

```yaml
requires:
  bins: [python3]
  packages:
    core: [pyreadstat>=1.3.5,<2, pyreadr>=0.4,<0.5, pandas>=2.0,<3]
    extended: [openpyxl, xlrd, scipy, h5py, pyarrow, lxml, odfpy, tableauhyperapi, dbfread, dbf, pyodbc]
```

> Full list: `requirements.txt` / 完整列表见 `requirements.txt`

## Detailed Docs / 详细文档

- **English**: [`README.md`](./README.md) — format limits, strategies, encoding, extension guide
- **中文**: [`README_ZH.md`](./README_ZH.md) — 格式限制、读入策略、编码注意事项、扩展指南

## Security / 安全

- **All R-invoking paths are opt-in & sandboxed by default / 所有调用 R 的路径默认隔离、需显式开启**: reading `.rda/.rds/.RData` (`readRDS()/load()`), reading Minitab `.mtw/.mpj` and EpiData `.rec` (`foreign::read.mtb()/read.epiinfo()`), and writing R formats (`.rda/.rds`) are **disabled by default**. They only run when you explicitly pass `allow_r_exec=True` on a TRUSTED file. Pure-Python parsers (`pyreadr`, `mtbpy`) are tried first and never execute code.
- **No silent R fallback / 无静默 R 回退**: If the pure-Python parser fails and `allow_r_exec` is not set, the skill raises a clear error instead of silently launching R — eliminating the risk of executing embedded code from untrusted files.
- **R scripts are static templates / R 脚本为静态模板**: When the opt-in R path is used, all R scripts are fully static templates; user inputs are passed only as CLI args (`commandArgs(trailingOnly=TRUE)` via `jsonlite`) — **never concatenated into executable R code**. Random temp filenames; no fixed paths.
- **R bridge writes a temp CSV / R 桥接写临时 CSV**: When R is used (opt-in), converted data is materialized to a temporary CSV on disk before being read back; the temp file is deleted immediately after use, but on crash or via backup/indexing tools it could briefly persist — avoid processing highly sensitive data through R-backed formats.
- **No destructive writes / 无破坏性写入**: Writing an existing `.hyper` first writes to a temp file; only after success is the existing file rotated to `<file>.bak` (prior `.bak` demoted to `.bak.1`, never silently deleted), then atomically swapped in. On write failure the original is untouched.
- **Pinned dependencies / 依赖已固定版本**: Core deps carry upper-bound pins (`pandas`, `pyreadstat`, `pyreadr`) — see `requirements.txt`.
- **Optional install / 可选安装**: `python scripts/check_env.py --install` only runs on explicit request.
- **Permissions required / 所需权限**: Read the input file; write the output file to a path you specify. No network access unless you explicitly request package installation. No destructive writes — existing `.hyper` outputs are backed up to `.bak` before overwrite.
- **Scope / 范围**: Statistical data formats only. Text/JSON formats preserve metadata subset only — see «Format Limits» in README.

## License / 许可证

MIT. See [`LICENSE`](./LICENSE). / 详见 [`LICENSE`](./LICENSE)。
