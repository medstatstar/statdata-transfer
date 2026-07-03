# statdata-transfer | Statistical Data Format Converter

Read 28+ statistical software and clinical trial data formats (CDISC ODM/EpiData/EpiInfo/Excel/EViews/Feather/FST/GraphPad Prism/Gretl/HDF5/HTML/jamovi/JMP/JSON/MATLAB/Minitab/ODS/ORC/Parquet/R/SAS/SPSS/Stata/Weka ARFF/XML) into Python/pandas DataFrame, and **convert between formats bidirectionally**, preserving 100% of retainable metadata.

**中文文档 | Chinese docs**: [README_ZH.md](README_ZH.md)

## Core Capabilities

### Read (Data Extraction)
Extract data + metadata from 28+ statistical formats into pandas DataFrame. SPSS/Stata/SAS preserve all metadata types; other formats clearly document what is preserved vs lost.

### Write / Convert (Format Conversion)
Convert read results to any other format:
- **Statistical formats inter-convert**: SPSS ↔ Stata ↔ R ↔ SAS XPT (preserve all metadata types)
- **Export universal formats**: Parquet, Feather, HDF5, JSON, CSV, TSV, Excel, etc. (metadata embedded in schema.metadata or sidecar JSON)
- **Universal formats → Statistical formats**: Reverse preserve metadata

### Auto Warnings
Automatically detects and reports what metadata can be preserved vs lost during conversion, avoiding silent data loss. All user-facing messages are bilingual (zh-cn/en).

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

> ✅=完整保留 Full preservation · ⚠️=部分保留或条件性 Partial/conditional · ✗=无法保留 Not preserved

## Return Structure

```python
{
    "dataframe": pd.DataFrame,
    "metadata": {
        "file_format": "spss_sav",
        "row_count": 100, "column_count": 10,
        "variable_labels": {"q1": "Question 1"},
        "value_labels": {"q1": {1: "Yes", 2: "No"}},
        # ... all metadata types
    },
    "warnings": [],
}
```

## Recommended Read Strategies

| Use Case | Recommendation |
|----------|---------------|
| Data warehousing / ETL | SPSS `.sav` or Stata `.dta` → Parquet / HDF5 |
| Scientific computing | `.mat` or `.hdf5` → NumPy / pandas |
| Statistical analysis (Python) | `.sav` / `.dta` → pandas (preserve metadata) → scipy.stats |
| Report output | pandas → JSON / HTML / Excel |
| Cross-software sharing | Stata ↔ SPSS ↔ R direct interconversion (no intermediate format) |

## File Size Limits

| Format | Memory Behavior |
|--------|----------------|
| pyreadstat (SPSS/Stata/SAS) | Loads entire file into RAM; limited by available memory |
| HDF5 | Supports chunked reading; not limited by RAM |
| Parquet | pyarrow supports memory-mapped reading (mmap); can handle files larger than RAM |

## Encoding Notes

- **Chinese files**: Old Stata/SAS files may use GBK/gb2312 instead of UTF-8. Use `encoding='gbk'` parameter.
- **European files**: Some SAS files use Latin-1. Try `encoding='latin1'` if UTF-8 fails.
- **Excel**: Encoding usually auto-detected.

## Recommended Practices

1. **Before reading**: Run `check_env.py` to verify dependencies.
2. **During reading**: Try `encoding='gbk'` (Chinese) or `encoding='latin1'` (European) if UTF-8 fails.
3. **After reading**: Check `result['warnings']` and column report for precision risks / special-missing columns.
4. **Old RData files**: v1.2+ auto-falls back to R; no manual conversion needed.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

For complete code examples, see `references/usage_examples.py`. Or run via WorkBuddy:

```
> convert data.sav to .dta
> read data.sav and show metadata
> are there any metadata loss concerns converting .sav to .xlsx?
```

## Extending

Want to add a new format? Edit `scripts/reader_*.py` to add a reader function, register it in the format_map in `scripts/reader_core.py`, and add a TypedDict in `scripts/reader_core.py`.

## Format Limitations

*Alphabetically ordered. See SKILL.md for the capability matrix.*

### CDISC ODM (.odm)
- **XML structure dependency**: `ItemGroupData`/`ItemData` nested parsing depends on ODM file structure regularity. Some complex `AttributeValue` structures may not be fully parsed.

### EpiData (.rec)
- **R foreign dependency**: Requires R environment for conversion via `foreign` package.

### EpiInfo (.prj)
- **External data file required**: `.prj` files contain no data. Automatically associates CSV files with the same name in the same directory.
- Falls back to header-field cross-validation if no same-name CSV exists.
- Access database files are not supported; export to CSV from EpiInfo first.

### Excel (.xlsx/.xls)
- **Merged cells**: Only top-left value retained; merged area cells become NaN.
- **Formulas**: Computed values only; formula definitions are lost.
- **Charts/shapes**: Not extracted.

### EViews (.wf1/.wf2)
- **JSON structure**: Parsed from EVWS format; page variable info extracted.

### Feather (.feather)
- **Version sensitivity**: Labels preserved in Arrow schema.metadata; version compatibility depends on pyarrow.

### FST (.fst)
- **R package**: Requires R `fst` package for read/write.

### GraphPad Prism (.pzfx)
- **Multi-table**: Pzfx files may contain multiple tables; current implementation extracts primary data.

### Gretl (.gdt)
- **XML/gzip dual-format**: Auto-detected.
- `.gdtb` binary format not directly readable; user prompted to export as XML via Gretl.

### HDF5 (.h5)
- **Hierarchical structure**: Nested groups are flattened to top-level variables.
- **Attributes**: HDF5 dataset attributes not extracted to metadata.

### HTML (.html)
- **Table extraction**: Reads HTML tables; formatting/styling discarded.

### jamovi (.omv)
- **ZIP archive**: Variable definitions from JSON structure fully extracted.

### JMP (.jmp)
- **Library dependency**: Relies on `jmpio-python`; target version support varies.

### JSON (.json)
- **Custom wrapper**: Uses `{"meta": {...}, "data": [...]}` wrapper for full metadata preservation.

### MATLAB (.mat)
- **v7.3+ (HDF5)**: scipy.io.loadmat cannot read v7.3+ files; use h5py directly.

### Minitab (.mtw)
- **R relay**: Converted via R environment.

### ODS (.ods)
- **OpenDocument**: Read via odfpy; formatting discarded.

### ORC (.orc)
- **Columnar**: Same Arrow schema.metadata label preservation as Parquet.

### Parquet (.parquet)
- **Nested types**: Map/Struct/List depth >2 may auto-flatten to multiple columns.
- **Partitioned datasets**: Directory-partitioned Parquet not yet supported (single file only).

### R (.rda/.rds)
- **ASCII XDR**: Old-format RDA files (`RDA2\nA\n` header) cannot be read by pyreadr; auto-fallback to R.
- **Factor level order**: R factor level order may not be preserved as pandas Categorical ordering.
- **Multi-object RDA**: Files may contain multiple objects; `read_all_r_objects()` returns all.

### SAS (.sas7bdat)
- **Catalog file**: Value labels in `.sas7bcat` must be co-located with data file for auto-load.
- **Viya CAS**: `.sashdat` and other new formats not supported.
- **DATE origin**: 1960-01-01 (same as Stata).

### SPSS (.sav)
- **MR Sets**: Imported as raw dictionary; semantics require manual reconstruction.
- **Inline formulas**: Variable calculation formulas lost; only computed results retained.
- **Special missing values**: Marked in `special_missing`; preserve on write.
- `.zsav` compressed: Not supported by pyreadstat; falls back to `.sav`.

### Stata (.dta)
- **Special missing values**: `.a`–`.z` become NaN; original distinction semantics lost.
- **String encoding**: Pre-v13 Stata may use Latin-1; specify `encoding='latin1'`.
- **Stata 117-119**: pyreadstat 1.3.5 not supported; auto-downgrade to version 15.

### Weka ARFF (.arff)
- **Type support**: NUMERIC/INTEGER/REAL/STRING/DATE/NOMINAL/RELATIONAL.
- **Nominal case**: Original case preserved; mapped to `pd.Categorical`.
- **Sparse format**: `{index value}` fully parsed.

### XML (.xml)
- **Structure-agnostic**: Reads well-formed XML; no schema assumed.

## License

MIT License. See [LICENSE](LICENSE) for details.
