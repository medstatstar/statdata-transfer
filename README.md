# statdata-transfer | Statistical Data Format Converter

[🇨🇳 中文 (Chinese)](./README_ZH.md)

---

Read 28+ statistical software and clinical trial data formats (CDISC ODM/EpiData/EpiInfo/Excel/EViews/Feather/FST/GraphPad Prism/Gretl/HDF5/HTML/jamovi/JMP/JSON/MATLAB/Minitab/ODS/ORC/Parquet/R/SAS/SPSS/Stata/Weka ARFF/XML) into Python/pandas DataFrame, and **bidirectionally convert between any formats** (SPSS↔Stata↔R↔SAS↔Excel↔Parquet↔HDF5↔JSON…), preserving 100% of retainable metadata.

Note: This skill does not require any statistical software to be installed, but its functionality is limited to data format conversion only. If you need **an AI agent to seamlessly integrate with and invoke the analysis capabilities of various installed statistical software**, it is strongly recommended to use the **statsoft-cli** skill, which is specifically designed for AI agents to seamlessly integrate statistical software.

## Core Capabilities

### Read (Data Extraction)
Extract data + all metadata (variable labels, value labels, special missing values, etc.) from 28+ statistical formats into pandas DataFrame as an intermediate format. Preserves metadata as completely as possible and clearly indicates what is preserved vs lost.

### Write / Convert (Format Conversion)
Convert read results to any other format:
- **Statistical formats inter-convert**: SPSS ↔ Stata ↔ R ↔ SAS XPT (preserve all metadata types)
- **Export universal formats**: Parquet, Feather, HDF5, JSON, CSV, TSV, Excel, etc. (metadata embedded in schema.metadata or sidecar JSON)
- **Universal formats → Statistical formats**: Reverse preserve metadata

### Auto Warnings
Automatically detects and reports what metadata can be preserved vs lost during conversion, avoiding silent data loss. All user-facing messages are bilingual (zh-cn/en).

## Supported Formats & Capability Matrix

*Sorted alphabetically.*

| Format | Extension | Dependency | Var Label | Val Label | Special Missing | Formula | Meta Preserve |
|--------|-----------|------------|-----------|-----------|-----------------|---------|---------------|
| CDISC ODM | `.odm` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Clinical data only |
| EpiData | `.rec` | R foreign | ✗ | ✗ | ✗ | ✗ | ⚠️ Via R |
| EpiInfo | `.prj` `.xml` | xml/etree | ✅ | ✅(codes) | ✗ | ✗ | ✅ XML structure |
| Excel | `.xlsx` `.xls` `.xlsm` | openpyxl / xlrd | ✗ | ✗ | ✗ | ⚠️ result only | ⚠️ Extra sheet for labels |
| EViews | `.wf1` `.wf2` | built-in | ✗ | ✗ | ✗ | ✗ | ⚠️ JSON structure |
| Feather | `.feather` `.arrow` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Version diff |
| FST | `.fst` | fst (R) | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Version diff |
| GraphPad Prism | `.pzfx` `.pz` | pzfx | ✗ | ✗ | ✗ | ✗ | ⚠️ Multi-table |
| Gretl | `.gdt` `.gdtb` | built-in | ✅ | ✅(tables) | ✗ | ✗ | ✅ string-tables |
| HDF5 | `.h5` `.hdf5` | h5py | ✗ | ✗ | ✗ | ✗ | ⚠️ Hierarchy, attrs on write |
| HTML | `.html` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Tables only |
| jamovi | `.omv` | ZIP built-in | ✅ | ✅ | ✗ | ✗ | ✅ JSON analysis |
| JMP | `.jmp` | jmpio-python | ⚠️ | ⚠️ | ✗ | ✗ | ⚠️ Multi-table |
| JSON | `.json` | built-in | ✅ | ✅ | ✗ | ✗ | ✅ stat-full-meta on write |
| MATLAB | `.mat` | scipy | ✗ | ✗ | ✗ | ✗ | ⚠️ Variable names |
| Minitab | `.mtw` `.mpj` | mtbpy / R | ✗ | ✗ | ✗ | ✗ | ⚠️ Via R |
| ODS | `.ods` | odfpy | ✗ | ✗ | ✗ | ✗ | ⚠️ Data only |
| ORC | `.orc` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Version diff |
| Parquet | `.parquet` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Nested types, schema.metadata on write |
| R | `.rda` `.rds` | pyreadr + R | ✅ | ✅ | ✅ | ✗ | ✅ statdata_meta, R bridge on write |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | pyreadstat | ✅ | ✅(need catalog) | ⚠️ | ✗ | ✅ |
| SPSS | `.sav` `.zsav` `.por` | pyreadstat | ✅ | ✅ | ✅ | ✗ | ✅ |
| Stata | `.dta` | pyreadstat | ✅ | ✅ | ⚠️ | ✗ | ✅ |
| Weka ARFF | `.arff` | built-in | ✅ | ✅(nominal) | ✗ | ✗ | ✅ nominal mapping |
| XML | `.xml` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Structure preserved |

> ✅=Full preservation · ⚠️=Partial/conditional · ✗=Not preserved

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
| Statistical analysis (Python) | `.sav` / `.dta` → pandas → scipy.stats |
| Report output | pandas → JSON / HTML / Excel |
| Cross-software sharing | Stata ↔ SPSS ↔ R direct interconversion |

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
**Read Limitations:**
- XML structure dependency: Nested parsing depends on ODM file structure regularity. Complex AttributeValue structures may not be fully parsed.
- Statistical metadata (variable labels, value labels) is not part of the ODM specification — only clinical data structure is preserved.

### EpiData (.rec)
**Read Limitations:**
- Requires R + `foreign` package as the only reader. No Python-native fallback available.
- Statistical metadata (variable labels, value labels) is lost during R-to-CSV bridge.

### EpiInfo (.prj)
**Read Limitations:**
- External data file required: `.prj` files contain no data. Automatically associates CSV files with the same name in the same directory.
- Falls back to header-field cross-validation if no same-name CSV exists.
- Access database files not supported; export to CSV first.

**Write Notes:**
- Variable labels and value labels stored in XML project structure can be reconstructed (codes/options definitions extracted).

### Excel (.xlsx/.xls)
**Read Limitations:**
- Merged cells: Only top-left value retained; merged area cells become NaN.
- Formulas: Computed values only; formula definitions are lost.
- Charts/shapes: Not extracted.

**Write Notes:**
- Variable/value labels stored in a separate metadata worksheet.

### HDF5 (.h5)
**Read Limitations:**
- Hierarchical structure: Nested groups are flattened to top-level variables.
- HDF5 dataset attributes are collected into `hdf5_metadata.file_attributes` but are not auto-parsed as variable labels. Only the `stat-full-meta` embedded format is auto-restored.

**Write Notes:**
- Root-level attributes used for metadata storage on write (via `h5py`).

### JMP (.jmp)
**Read Limitations:**
- Requires `jmpio-python` library; target version support varies.
- Multi-table JMP files: only the first table is returned (additional table metadata preserved in `jmp_metadata`).

**Write Notes:**
- Single-table write only. Multi-table structures may lose table-level metadata.

### MATLAB (.mat)
**Read Limitations:**
- v7.3+ (HDF5-based): `scipy.io.loadmat` cannot read these files. No fallback to `h5py` is implemented in the current code path.
- Complex structures (nested cells, sparse matrices, function handles) fall back to single-column flattened output.
- Object classes and datetime columns lose type fidelity during conversion.

### Parquet (.parquet)
**Read Limitations:**
- Deeply nested types (>2 levels of `list<struct>`) become opaque Python object columns when converted via `pyarrow.to_pandas()`. Arrow schema fidelity is preserved, but pandas representation may lose structure.
- Directory-partitioned Parquet datasets not yet supported (single file only).

### R (.rda/.rds)
**Read Limitations:**
- Old-format ASCII XDR (RDA2) files: `pyreadstat` cannot read them. **Auto-fallback to R** works when R is installed (recommended). Without R, these files fail.
- Factor level order may not be preserved as `pandas.Categorical` ordering unless embedded via `stat-full-meta`.
- Multi-object RDA files: `read_all_r_objects()` returns all objects as a list.

**Write Notes:**
- Write operations routed through R bridge (`statdata_meta` attribute) for full metadata round-trip.

### SAS (.sas7bdat)
**Read Limitations:**
- Value labels require a co-located `.sas7bcat` catalog file (auto-searched in same directory). Without catalog, value labels are absent.
- Viya CAS `.sashdat` and other new SAS formats are not supported by `pyreadstat`.
- DATE origin: 1960-01-01 (same as Stata).

### SPSS (.sav/.zsav/.por)
**Read Limitations:**
- MR Sets imported as raw dictionary; semantics not preserved (pyreadstat limitation). Data is retained but structure requires manual reconstruction.
- Variable calculation formulas are lost; only computed results retained.
- Special missing values (`.A`–`.Z`, system missing) flagged in `special_missing`; must be explicitly preserved on write.
- `.zsav` read requires gzip decompression (pyreadstat 1.2+ or auto-fallback to tempfile decompression).
- `.por` (older SPSS portable format): variable type mapping simplified; some metadata fields absent.

**Write Notes:**
- `.zsav` write requires pyreadstat 1.2+; otherwise auto-fallback to uncompressed `.sav`.

### Stata (.dta)
**Read Limitations:**
- Special missing values (`.a`–`.z`): when `user_missing=True` (default), these are preserved as character tags in the DataFrame. When `user_missing=False`, they become NaN and original distinction is **lost irreversibly**.
- String encoding: Pre-v13 Stata files may use Latin-1; specify `encoding='latin1'`.
- Stata 117-119 (newest format): not supported by pyreadstat 1.3.5; auto-downgrade to version 15 on write.

**Write Notes:**
- When `user_missing=True`, special missing tags are written back correctly via `missing_user_values` parameter.

## License

MIT-0 License. See [LICENSE](LICENSE) for details.
