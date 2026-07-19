# statdata-transfer / Statistical Data Format Converter

[🇨🇳 中文 (Chinese)](./README_ZH.md)

---

Read 50+ statistical software and clinical trial data formats into Python/pandas DataFrame, and **inter-convert between most formats** (SPSS↔Stata↔R↔SAS XPT↔Excel↔Parquet↔HDF5↔JSON…). For statistical binary formats (SPSS/Stata/SAS/R/Excel/Parquet/HDF5/…) it preserves full variable/value labels and missing-value metadata; text formats (CSV/XML/HTML/ODS) and JSON preserve only a retainable subset — see Format Limits below. **12 proprietary formats** (SAS CPORT, Statistica, OxMetrics, SYSTAT, Paradox, LIMDEP, NCSS, FST, etc.) are **detect-only** — the skill recognizes the extension and provides clear export guidance, but does not parse the data.

Note: This skill does not require any statistical software, but handles data format conversion only. If you need **an AI agent to integrate with installed statistical software for analysis**, use the **[statsoft-cli](https://github.com/medstatstar/statsoft-cli)** skill instead.

## Core Capabilities

### Read (Data Extraction)
Extract data + all metadata from 50+ formats into pandas DataFrame. Preserves metadata as completely as possible and clearly indicates what is preserved vs lost.

### Write / Convert (Format Conversion)
- **Inter-convert stats formats**: SPSS ↔ Stata ↔ R ↔ SAS XPT (all metadata types preserved)
- **Export universal formats**: Parquet, Feather, HDF5, JSON, CSV, TSV, Excel (metadata embedded in schema.metadata or sidecar JSON)
- **Universal → stats formats**: Reverse preserve metadata via embedded `stat-full-meta`

### Auto Warnings
Automatically detects and reports metadata preservation vs loss during conversion. All user-facing messages are bilingual (en/zh-cn).

## Supported Formats & Capability Matrix

*Sorted alphabetically.*

| Format | Extension | Dependency | Var Label | Val Label | Special Missing | Formula | Meta Preserve |
|--------|-----------|------------|-----------|-----------|-----------------|---------|---------------|
| CDISC ODM | `.odm` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Clinical data only |
| dBASE / FoxPro | `.dbf` | dbfread / dbf | ✗ | ✗ | ✗ | ✗ | ⚠️ Read+Write; uppercase names |
| EpiData | `.rec` | R foreign | ✗ | ✗ | ✗ | ✗ | ⚠️ Via R |
| EpiInfo | `.prj` `.xml` | xml/etree | ✅ | ✅(codes) | ✗ | ✗ | ✅ XML structure |
| Excel | `.xlsx` `.xls` `.xlsm` | openpyxl / xlrd | ✗ | ✗ | ✗ | ⚠️ result only | ⚠️ Extra sheet for labels; merged-cell fill |
| EViews | `.wf1` `.wf2` | built-in | ✗ | ✗ | ✗ | ✗ | ⚠️ JSON structure |
| Feather | `.feather` `.arrow` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Version diff |
| FST | `.fst` | — | ✗ | ✗ | ✗ | ✗ | ✗ Detect-only (proprietary format) |
| GraphPad Prism | `.pzfx` `.pz` | pzfx | ✗ | ✗ | ✗ | ✗ | ⚠️ Multi-table |
| Gretl | `.gdt` `.gdtb` | built-in | ✅ | ✅(tables) | ✗ | ✗ | ✅ string-tables |
| HDF5 | `.h5` `.hdf5` | h5py | ✗ | ✗ | ✗ | ✗ | ⚠️ Hierarchy + attribute labels |
| HTML | `.html` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Tables only |
| jamovi | `.omv` | ZIP built-in | ✅ | ✅ | ✗ | ✗ | ✅ JSON analysis |
| JMP | `.jmp` | jmpio-python | ⚠️ | ⚠️ | ✗ | ✗ | ⚠️ Multi-table |
| JSON | `.json` | built-in | ✅ | ✅ | ✗ | ✗ | ✅ stat-full-meta on write |
| MATLAB | `.mat` | scipy | ✗ | ✗ | ✗ | ✗ | ⚠️ v7.3+ via h5py fallback |
| Mathematica | `.wdx` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Best-effort XML |
| Minitab | `.mtw` `.mpj` | mtbpy / R | ✗ | ✗ | ✗ | ✗ | ⚠️ Via R |
| MS Access | `.mdb` `.accdb` | pyodbc + Access Driver | ✗ | ✗ | ✗ | ✗ | ⚠️ Multi-table; needs system driver |
| ODS | `.ods` | odfpy | ✗ | ✗ | ✗ | ✗ | ⚠️ Data only |
| ORC | `.orc` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Version diff |
| Origin | `.opju` `.oggu` | zipfile + lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Best-effort |
| Parquet | `.parquet` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ Nested types; partitioned datasets |
| R | `.rda` `.rds` `.rdata` | pyreadr + R | ✅ | ✅ | ✅ | ✗ | ✅ statdata_meta + R bridge |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | pyreadstat | ✅ | ✅(need catalog) | ⚠️ | ✗ | ✅ |
| SPSS | `.sav` `.zsav` `.por` | pyreadstat | ✅ | ✅ | ✅ | ✗ | ✅ |
| Stata | `.dta` | pyreadstat | ✅ | ✅ | ⚠️ | ✗ | ✅ |
| Weka ARFF | `.arff` | built-in | ✅ | ✅(nominal) | ✗ | ✗ | ✅ nominal mapping |
| XML | `.xml` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Structure preserved |

> ✅=Full preservation · ⚠️=Partial/conditional · ✗=Not preserved

### Detect-Only Formats
Formats with no parser available. The skill detects the extension and provides clear export guidance (no data parsing).

| Format | Extension | Guidance |
|--------|-----------|----------|
| FST (R fst package) | `.fst` | R: `fst::read_fst("in.fst", "out.csv")` then read CSV |
| LIMDEP / NLOGIT | `.lpw` | Export to CSV from original software |
| NCSS | `.ncss` | Export to CSV |
| OxMetrics | `.in7` | Export to CSV / `.dta` |
| Paradox | `.db` `.px` | Export to `.dbf` / CSV |
| SAS CPORT | `.cpt` | SAS: `proc export` to XPORT(`.xpt`) / `.sas7bdat` |
| Statistica | `.sta` | Export to `.sav` / `.csv` |
| SYSTAT | `.sys` `.syd` | Export to CSV / `.sav` |

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
    "column_report": {"q1": {"source_type": "int", "pandas_dtype": "int64"}},
}
```

## Metadata Preservation Tiers

### Read Fallback Rules
1. **Statistical binary formats** (SPSS/Stata/SAS/R): 100% metadata preserved
2. **Arrow ecosystem** (Parquet/Feather/ORC): Only restores labels from `write_stat_file`
3. **Non-stats formats** (CSV/Excel/XML/HTML/ODS): Data only; use `apply_value_labels()` to attach manually
4. **R formats**: v1.6.0+ embeds all metadata via `statdata_meta` attribute

### Metadata-Loss Warnings
Runtime `warnings` list includes:
- Special missing values → NaN
- Measurement level / display width / alignment lost
- MR sets cannot be preserved
- File label / notes not preserved
- Date origin not saved

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
| pyreadstat (SPSS/Stata/SAS) | Loads entire file into RAM |
| HDF5 | Chunked reading; not limited by RAM |
| Parquet | pyarrow memory-mapped (mmap); handles files >RAM |

## Encoding Notes

- **Chinese files**: Old Stata/SAS may use GBK/gb2312. Use `encoding='gbk'`.
- **European files**: Some SAS files use Latin-1. Try `encoding='latin1'` if UTF-8 fails.
- **Auto-detection**: `_auto_detect_encoding` is enabled by default for SPSS/Stata/SAS.

## Providing Input Files

AI agents (e.g., WorkBuddy) can only directly upload a limited set of file types. When your data file cannot be uploaded directly, you have two options:

1. **Use the absolute file path** in your prompt (e.g., `convert C:/Users/Name/Desktop/data.sav to .dta`)
2. **Compress the file as a `.zip` archive** and upload the zip instead

The skill automatically extracts and processes zip archives containing a single data file.

## Quick Start

```bash
# Check environment
python scripts/check_env.py --install
```

Complete code examples: [`references/usage_examples.py`](./references/usage_examples.py)

WorkBuddy prompts:
```
> convert data.sav to .dta
> read data.sav and show metadata
> are there any metadata loss concerns converting .sav to .xlsx?
```

## Extending

To add a new format: edit `scripts/reader_*.py` to add a reader function, register it in `format_map` in `scripts/reader_core.py`, and add a TypedDict in `scripts/reader_core.py`.

## Format Limitations

*Alphabetically ordered. Markeds ✅ = fixed, 🔄 = new capability; rest are inherent format limits.*

### CDISC ODM (.odm)
**Read:**
- ❌ XML structure dependency: nested parsing depends on ODM regularity
- ❌ No statistical metadata in ODM spec; only clinical structure preserved

### dBASE / FoxPro (.dbf)
**Read:**
- ❌ Field names forced to uppercase (format limitation)
- ✅ Read + Write supported

### EpiData (.rec)
**Read:**
- ❌ Requires R + `foreign` package; no Python-native fallback
- ❌ Statistical metadata lost in R-to-CSV bridge

### EpiInfo (.prj)
**Read:**
- ❌ Project file contains no data; auto-associates same-name CSV
- ❌ Access not supported; export to CSV first
**Write:**
- ✅ Variable labels and codes reconstructed in XML structure

### Excel (.xlsx/.xls/.xlsm)
**Read:**
- ✅ **Merged cells**: Fills merged area with anchor value; toggle via `fill_merged_cells=True` (default)
- ❌ Formulas lost; only computed values retained
- ❌ Charts/shapes not extracted
**Write:**
- Variable/value labels in separate metadata worksheet

### HDF5 (.h5/.hdf5)
**Read:**
- ✅ **Multi-dataset fallback**: When `pd.read_hdf` fails, h5py fallback merges all top-level numeric datasets
- ✅ **Attribute labels**: Scans common keys (`label`, `description`, `units`, `ColumnLabel`…)
- ❌ Hierarchy flattened to top-level
**Write:**
- Root-level attributes used for metadata storage

### JMP (.jmp)
**Read:**
- ❌ Requires `jmpio-python`; version support varies
- ❌ Multi-table: only first table returned
**Write:**
- Single-table only

### MATLAB (.mat)
**Read:**
- ✅ **v7.3+ (HDF5-based)**: Detects `MATLAB 7.3` header or scipy failure → h5py path
- ❌ Complex structures (nested cells, sparse, fn handles) → single-column flattened
- ❌ Object classes and datetime lose type fidelity

### Parquet (.parquet)
**Read:**
- ❌ Deeply nested types (>2 levels `list<struct>`) → opaque Python objects
- ✅ **Partitioned datasets**: Directory with `part-*.parquet` via `pyarrow.dataset`

### R (.rda/.rds/.rdata)
**Read:**
- ✅ Old ASCII XDR (RDA2): read via R bridge requires `allow_r_exec=True` (opt-in; not automatic)
- ❌ Factor level order may not be preserved as Categorical unless embedded via `stat-full-meta`
- ❌ Multi-object RDA: `read_all_r_objects()` returns all
**Write:**
- R bridge (`statdata_meta` attribute) for full metadata round-trip

### SAS (.sas7bdat/.xpt/.sas7bcat)
**Read:**
- ✅ Value labels require co-located `.sas7bcat` (auto-detected)
- ❌ Viya CAS `.sashdat` not supported
- Date origin: 1960-01-01

### SPSS (.sav/.zsav/.por)
**Read:**
- ❌ MR Sets imported as raw dict; semantics not preserved
- ❌ Formulas lost; only computed results retained
- ⚠️ Special missing (`.A`–`.Z`) flagged in `special_missing`; must be preserved explicitly on write
**Write:**
- `.zsav` requires pyreadstat 1.2+; else auto-fallback to `.sav`

### Stata (.dta)
**Read:**
- ⚠️ Special missing (`.a`–`.z`): preserved when `user_missing=True` (default); becomes NaN when `user_missing=False` (irreversible)
- ✅ Pre-v13 Latin-1 auto-detected
- ❌ Stata 117-119 not supported by pyreadstat 1.3.5; auto-downgrade to v15 on write

## Security

- **R execution is opt-in and sandboxed by default.** Every path that invokes the local R interpreter — reading `.rda/.rds/.RData` (via `readRDS()/load()`), reading Minitab `.mtw/.mpj` and EpiData `.rec` (via `foreign::read.mtb()/read.epiinfo()`), and writing R formats (`.rda/.rds`) — is **disabled by default**. It only runs when you explicitly pass `allow_r_exec=True` on a TRUSTED file. Pure-Python parsers (`pyreadr`, `mtbpy`) are tried first and never execute code.
- **No silent R fallback.** If the pure-Python parser fails and `allow_r_exec` is not set, the skill raises a clear error instead of silently launching R. This removes the risk of executing embedded code from untrusted files.
- **R scripts are static templates.** When the opt-in R path runs, all R scripts are fully static; user inputs (file paths, labels, metadata) are passed only as CLI args (`commandArgs(trailingOnly=TRUE)` via `jsonlite`) — never concatenated into executable R code. Random temp filenames; no fixed paths.
- **Temporary CSV exposure (R bridge).** When R is used (opt-in), converted data is materialized to a temporary CSV on disk before being read back. The temp file is deleted immediately after use, but on crash or via backup/indexing tools it could briefly persist. Avoid processing highly sensitive data through R-backed formats, or prefer a non-R path.
- **No destructive writes.** When writing a `.hyper` file that already exists, the new data is written to a temp file first; only after success is the existing file rotated to `<file>.bak` (the previous `.bak` is demoted to `.bak.1`, never silently deleted), then the temp file is atomically swapped in. If the write fails, the original file is left untouched.
- **Optional package install.** `python scripts/check_env.py --install` runs only on explicit request.
- **Pinned dependencies.** Core dependencies carry upper-bound pins (`pandas`, `pyreadstat`, `pyreadr`) — see `requirements.txt`.
- **Scope.** Statistical data formats only. No network access unless you explicitly request package installation.

## License

MIT-0 License. See [LICENSE](LICENSE) for details.
