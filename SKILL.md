---
name: statdata-transfer
cn_name: 统计数据格式转换器 
description: "将 28+ 统计软件格式读入 pandas DataFrame，完整保留全部元数据；支持任意双向转换。Read 28+ stats formats into pandas with full metadata; bidirectional conversion. See README.md / README_ZH.md for details."
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
    "openclaw": { "emoji": "🛠️"},
    "authors": ["medstatstar", "phoe-zip"],
    "version": "1.7.0",
    "license": "MIT",
    "tags": ["data-conversion", "statistics", "spss", "stata", "sas", "clinical-trials", "metadata", "pandas", "bidirectional"],
    "logo": "assets/logo.svg",
    "homepage": "https://github.com/medstatstar/statdata-transfer",
  }
---

# 统计数据格式转换器 | statdata-transfer

> 致敬 Stat/Transfer — 业界格式转换标杆 | Honoring Stat/Transfer — the industry standard

## 核心能力 | Core Capabilities

| 能力 | 说明 | Ability | Description |
|------|------|---------|-------------|
| 读入 | SPSS/Stata/SAS 100% 保留变量标签、值标签、缺失值等全部元数据 | Read | SPSS/Stata/SAS: 100% preserve all metadata |
| 转存 | 任意格式互转（.sav ↔ .dta ↔ .rda ↔ .xlsx ↔ .parquet 等） | Convert | Bidirectional conversion between any formats |
| 元数据嵌入 | Parquet/Feather/HDF5/JSON 通过 schema.metadata 保留标签 | Embed | Arrow/HDF5/JSON embed labels in schema.metadata |
| 丢失警告 | 转换时自动检测并报告元数据损失 | Warn | Automatic metadata-loss warnings on conversion |
| P0 修复 | R 对象读入、CSV 重复读取、值标签键还原等 | P0 Fixes | R object read, CSV dedup, value-label key restore |
| EpiInfo/ARFF/Gretl | 新增 3 种流行病学/ML/计量格式读入 | EpiInfo/ARFF/Gretl | New epidemiology/ML/econometrics format readers |

## 推荐场景 | Recommended Use Cases

| 场景 Scenario | 推荐 Recommendation | 说明 Notes |
|--------------|-------------------|------------|
| 保存中间数据 Intermediate data | **JSON** | 全部元数据双向 100% 还原 / All metadata, 100% bidirectional |
| 统计软件交换 Stats software swap | **SPSS/Stata/R** | 无损转换 / Lossless conversion |
| 高性能处理 High performance | **Parquet** | 高效 + 标签保留 / Fast + label preservation |
| 大数据集 Large datasets | **HDF5** | 支持分块 / Chunked storage |
| 临床数据 Clinical trials | **SAS XPT / CDISC ODM** | 监管提交 compliant submission |

## 触发条件 | Triggers

- 读入 `.dta` `.sav` `.sas7bdat` `.rda` `.xlsx` `.mat` `.h5` `.parquet` `.json` `.xml` 等 28+ 格式 / Read files: `.dta` `.sav` `.sas7bdat` `.rda` `.xlsx` `.mat` `.h5` `.parquet` `.json` `.xml` + 20 more
- 需要格式转换并保留元数据 / Format conversion with metadata preservation
- 需要不同统计软件间迁移数据 / Migrate data between statistical software
- 用户询问各格式读入能力边界 / User asks about format capability limits

## 支持格式与能力对照表 | Supported Formats & Capability Matrix

*按字母排序 | Sorted alphabetically.*

| 格式 Format | 扩展名 Extension | 依赖 Dependency | 变量标签 Var Label | 值标签 Val Label | 特殊缺失 Special Missing | 公式 Formula | 元数据保留 Meta Preserve |
|-------------|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|
| CDISC ODM | `.odm` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅临床数据 Clinical data only |
| EpiData | `.rec` | R foreign | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过R读入 Via R |
| EpiInfo | `.prj` `.xml` | xml/etree | ✅ | ✅(codes) | ✗ | ✗ | ✅ XML结构 XML structure |
| Excel | `.xlsx` `.xls` `.xlsm` | openpyxl / xlrd | ✗ | ✗ | ✗ | ⚠️ 仅结果 result only | ⚠️ 写出用额外工作表 Extra sheet for labels |
| EViews | `.wf1` `.wf2` | 内置 built-in | ✗ | ✗ | ✗ | ✗ | ⚠️ JSON结构 JSON structure |
| Feather | `.feather` `.arrow` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 Version diff |
| FST | `.fst` | fst (R) | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 Version diff |
| GraphPad Prism | `.pzfx` `.pz` | pzfx | ✗ | ✗ | ✗ | ✗ | ⚠️ 多表 Multi-table |
| Gretl | `.gdt` `.gdtb` | 内置 built-in | ✅ | ✅(tables) | ✗ | ✗ | ✅ string-tables |
| HDF5 | `.h5` `.hdf5` | h5py | ✗ | ✗ | ✗ | ✗ | ⚠️ 层级结构 Hierarchy，写出用文件属性 attrs on write |
| HTML | `.html` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅表格 Tables only |
| jamovi | `.omv` | ZIP内置 ZIP built-in | ✅ | ✅ | ✗ | ✗ | ✅ JSON分析 JSON analysis |
| JMP | `.jmp` | jmpio-python | ⚠️ | ⚠️ | ✗ | ✗ | ⚠️ 多表 Multi-table |
| JSON | `.json` | 内置 built-in | ✅ | ✅ | ✗ | ✗ | ✅ 写出嵌入stat-full-meta stat-full-meta on write |
| MATLAB | `.mat` | scipy | ✗ | ✗ | ✗ | ✗ | ⚠️ 变量名 Variable names |
| Minitab | `.mtw` `.mpj` | mtbpy / R | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过R读入 Via R |
| ODS | `.ods` | odfpy | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅数据 Data only |
| ORC | `.orc` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 Version diff |
| Parquet | `.parquet` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 嵌套类型 Nested types，写出用schema.metadata schema.metadata on write |
| R | `.rda` `.rds` `.rdata` | pyreadr + R | ✅ | ✅ | ✅ | ✗ | ✅ statdata_meta，写出通过R桥接 R bridge on write |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | pyreadstat | ✅ | ✅(需catalog need catalog) | ⚠️ | ✗ | ✅ |
| SPSS | `.sav` `.zsav` `.por` | pyreadstat | ✅ | ✅ | ✅ | ✗ | ✅ |
| Stata | `.dta` | pyreadstat | ✅ | ✅ | ⚠️ | ✗ | ✅ |
| Weka ARFF | `.arff` | 内置 built-in | ✅ | ✅(nominal) | ✗ | ✗ | ✅ 名义映射 nominal mapping |
| XML | `.xml` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 结构保留 Structure preserved |

> ✅=完整保留 Full preservation · ⚠️=部分保留或依赖条件 Partial/conditional · ✗=无法保留 Not preserved

## 返回结构 | Return Structure

```python
{
    "dataframe": pd.DataFrame,
    "metadata": {
        "file_format": "spss_sav",
        "collected_at": "2026-07-02T21:00:00",
        "row_count": 100, "column_count": 10,
        "total_missing_pct": 5.2,
        "variable_labels": {"q1": "问题1"},
        "value_labels": {"q1": {1: "是", 2: "否"}},
        # ... 全部元数据 | all metadata types
    },
    "warnings": [],
    "column_report": {"q1": {"source_type": "int", "pandas_dtype": "int64"}},
}
```

## 元数据保留能力 | Metadata Preservation

### 读入降损规则 | Read Fallback Rules

1. **统计软件格式**（SPSS/Stata/SAS）：全部元数据完整读入 | Stats formats: 100% metadata
2. **Arrow 生态**（Parquet/Feather/ORC/FST）：仅还原 write_stat_file 写入的标签 | Only restores labels from write_stat_file
3. **非统计格式**：仅保留数据值，可通过 `apply_value_labels()` 手动附加 | Data only; use apply_value_labels() manually
4. **R 格式**：v1.6.0+ 通过 `statdata_meta` 属性嵌入全部元数据 | v1.6.0+ embeds all metadata fields via statdata_meta

## 元数据丢失警告 | Metadata-Loss Warnings

运行时 `warnings` 列表自动包含以下提示 | Runtime `warnings` include:
- 特殊缺失值变为 NaN | Special missing → NaN
- 测量级别/显示宽度/对齐方式丢失 | Measurement level/width/alignment lost
- 多重响应集（mr_sets）无法保留 | MR sets cannot be preserved
- 文件标签/注释不保留 | File label/notes not preserved
- 日期基准不保存 | Date origin not saved

> 预检代码见 `references/usage_examples.py` 中「元数据丢失检查」部分 | Pre-check code: see "Metadata loss check" in `references/usage_examples.py`

## 依赖 | Dependencies

```yaml
requires:
  bins: [python3]
  packages:
    core: [pyreadstat>=1.3.5, pyreadr, pandas]
    extended: [openpyxl, xlrd, scipy, h5py, pyarrow, lxml, odfpy]
    optional: [jmpio-python, mtbpy, pzfx]
```

> 完整依赖列表见 `requirements.txt` | Full list: `requirements.txt`

## 参考文档 | References

- `references/usage_examples.py` — 完整代码示例 | Complete code examples
- `references/new_formats_architecture_analysis.json` — 架构分析 | Architecture analysis
