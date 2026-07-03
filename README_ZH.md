# statdata-transfer | 统计数据格式转换器

[🇬🇧 English](./README.md)

---

读入 28+ 统计软件及临床试验数据格式（CDISC ODM/EpiData/EpiInfo/Excel/EViews/Feather/FST/GraphPad Prism/Gretl/HDF5/HTML/jamovi/JMP/JSON/MATLAB/Minitab/ODS/ORC/Parquet/R/SAS/SPSS/Stata/Weka ARFF/XML），转换为 Python/pandas DataFrame，并在不同格式之间**双向转换**，100% 保留变量标签、值标签等元数据。

注意：本技能不需要任何统计软件的支持，但功能仅限于数据格式转换。如果需要**AI智能体接入并无缝调用已安装的各种统计软件的分析功能，**，强烈建议使用技能 **statsoft-cli**。该技能专为AI智能体无缝集成统计软件设计。

## 核心能力

### 读入（数据提取）
从 28+ 统计软件格式中提取数据 + 元数据（变量标签、值标签、特殊缺失值…等全部元数据），转为 pandas DataFrame+作为中间格式，尽可能完整保留元数据，并明确标注保留/丢失情况。

### 转存（格式转换）
将读入结果写出为任意其他格式：
- **统计格式互转**：SPSS ↔ Stata ↔ R ↔ SAS XPT（保留全部元数据）
- **导出通用格式**：Parquet、Feather、HDF5、JSON、CSV、TSV、Excel 等（元数据嵌入 schema.metadata 或 sidecar JSON）
- **通用格式→统计格式**：反向保留元数据

### 自动警告
转换时检测并报告哪些元数据可以保留、哪些会丢失，避免静默的数据损失。所有警告信息均为中英双语。

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
| Minitab | `.mw` `.mpj` | mtbpy / R | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过R读入 Via R |
| ODS | `.ods` | odfpy | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅数据 Data only |
| ORC | `.orc` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 Version diff |
| Parquet | `.parquet` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 嵌套类型 Nested types，写出用schema.metadata schema.metadata on write |
| R | `.rda` `.rds` | pyreadr + R | ✅ | ✅ | ✅ | ✗ | ✅ statdata_meta，写出通过R桥接 R bridge on write |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | pyreadstat | ✅ | ✅(需catalog need catalog) | ⚠️ | ✗ | ✅ |
| SPSS | `.sav` `.zsav` `.por` | pyreadstat | ✅ | ✅ | ✅ | ✗ | ✅ |
| Stata | `.dta` | pyreadstat | ✅ | ✅ | ⚠️ | ✗ | ✅ |
| Weka ARFF | `.arff` | 内置 built-in | ✅ | ✅(nominal) | ✗ | ✗ | ✅ 名义映射 nominal mapping |
| XML | `.xml` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 结构保留 Structure preserved |

> ✅=完整保留 Full preservation · ⚠️=部分保留或条件性 Partial/conditional · ✗=无法保留 Not preserved

## 返回结构

```python
{
    "dataframe": pd.DataFrame,
    "metadata": {
        "file_format": "spss_sav",
        "row_count": 100, "column_count": 10,
        "variable_labels": {"q1": "问题1"},
        "value_labels": {"q1": {1: "是", 2: "否"}},
        # ... 全部元数据
    },
    "warnings": [],
}
```


## 推荐读入策略

| 需求 | 推荐 |
|------|------|
| 数据入库/ETL | SPSS `.sav` 或 Stata `.dta` → Parquet / HDF5 |
| 科学计算 | `.mat` 或 `.hdf5` → NumPy / pandas |
| 统计分析（Python） | `.sav` / `.dta` → pandas → scipy.stats |
| 报告输出 | pandas → JSON / HTML / Excel |
| 跨软件共享 | Stata ↔ SPSS ↔ R 直接互转 |

## 文件大小限制

| 格式 | 内存行为 |
|------|---------|
| pyreadstat (SPSS/Stata/SAS) | 全文件加载到 RAM；受可用内存限制 |
| HDF5 | 支持分块读取；不受 RAM 限制 |
| Parquet | pyarrow 支持 mmap 映射模式；可处理 >内存的文件 |

## 编码注意事项

- **中文文件**：旧版 Stata/SAS 可能使用 GBK/gb2312。使用 `encoding='gbk'`。
- **欧洲文件**：部分 SAS 文件使用 Latin-1。UTF-8 失败时尝试 `encoding='latin1'`。
- **Excel**：通常自动检测。

## 推荐做法

1. **读入前**：使用 `check_env.py` 确认环境就绪。
2. **读入时**：UTF-8 失败时尝试 `encoding='gbk'`（中文）或 `encoding='latin1'`（欧洲）。
3. **读入后**：检查 `result['warnings']` 和列报告中的精度风险/特殊缺失列。
4. **旧版 RData**：v1.2+ 自动回退到 R 处理，无需手动转换。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

完整代码示例见 `references/usage_examples.py`。或在 WorkBuddy 对话中直接调用：

```
> convert data.sav to .dta
> read data.sav and show metadata
> are there any metadata loss concerns converting .sav to .xlsx?
```

## 扩展

需要支持新格式？编辑 `scripts/reader_*.py` 添加读入函数，在 `scripts/reader_core.py` 的 `format_map` 中注册，并在 `scripts/reader_core.py` 中补充对应的 TypedDict 定义。

## 格式限制与解决方案

### CDISC ODM (.odm)
- XML 结构依赖，部分复杂 ODM 文件的嵌套结构可能解析不完整。

### EpiData (.rec)
- 需通过 R `foreign` 包转换，需要 R 环境。

### EpiInfo (.prj)
- 项目文件不含数据，需关联外部 CSV。
- 自动搜索同名 CSV 或交叉验证目录内 CSV。
- Access 不支持，需先导出 CSV。

### Excel (.xlsx)
- 合并单元格仅保留左上角值，其余为 NaN。
- 公式丢失，仅保留计算结果。
- 图表/形状不提取。

### EViews (.wf1/.wf2)
- JSON 结构（EVWS 格式），变量信息可完整提取。

### Feather (.feather)
- 标签存于 Arrow schema.metadata，版本兼容性取决于 pyarrow。

### FST (.fst)
- 需要 R `fst` 包读写。

### GraphPad Prism (.pzfx)
- 可能含多表，当前读入主数据表。

### Gretl (.gdt)
- XML/gzip 双格式自动检测。
- `.gdtb` 二进制不可读，需先导出为 XML。

### HDF5 (.h5)
- 层级结构展平为顶级变量。
- 属性未提取为元数据。

### HTML (.html)
- 读取 HTML 表格，格式样式丢失。

### jamovi (.omv)
- 内置 ZIP，JSON 变量定义完整读入。

### JMP (.jmp)
- 依赖 jmpio-python，版本支持不一。

### JSON (.json)
- 使用 `{"meta":..., "data":[...]}` 包裹结构保留元数据。

### MATLAB (.mat)
- v7.3+ 基于 HDF5，scipy.io.loadmat 无法读取，需用 h5py。

### Minitab (.mw)
- 需 R 环境中转。

### ODS (.ods)
- 通过 odfpy 读入，格式丢失。

### ORC (.orc)
- 列存格式，标签存 Arrow schema.metadata。

### Parquet (.parquet)
- 嵌套类型 >2 层可能自动展平。
- 分区数据集暂未支持（仅单文件）。

### R (.rda/.rds)
- 旧版 ASCII XDR (RDA2) pyreadr 不支持，自动回退 R。
- factor 顺序可能未保留为 Categorical 顺序。
- 多对象 RDA：`read_all_r_objects()` 返回全部。

### SAS (.sas7bdat)
- 值标签定义在 `.sas7bcat`，需与数据文件同目录自动加载。
- Viya CAS 新格式不支持。
- 日期基准：1960-01-01。

### SPSS (.sav)
- MR Sets 读入为原始字典，语义需手动重建。
- 公式丢失，仅保留计算结果。
- 特殊缺失值标记需保留。
- `.zsav` 不支持，降级到 `.sav`。

### Stata (.dta)
- `.a`-`.z` 特殊缺失值读入后变 NaN。
- 旧版 (pre-v13) 可能 Latin-1 编码，需指定 `encoding='latin1'`。
- Stata 117-119 不支持，降级到 version 15。

### Weka ARFF (.arff)
- 支持 NUMERIC/STRING/NOMINAL/DATE/RELATIONAL。
- 名义变量保留原始大小写，映射为 Categorical。
- 稀疏格式 `{index value}` 完整解析。

### XML (.xml)
- 读取良构 XML，无 schema 假设。

## 许可证

MIT License。详见 [LICENSE](LICENSE)。
