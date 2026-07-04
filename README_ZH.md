# statdata-transfer | 统计数据格式转换器

[🇬🇧 English](./README.md)

---

读入 28+ 统计软件及临床试验数据格式（CDISC ODM/EpiData/EpiInfo/Excel/EViews/Feather/FST/GraphPad Prism/Gretl/HDF5/HTML/jamovi/JMP/JSON/MATLAB/Minitab/ODS/ORC/Parquet/R/SAS/SPSS/Stata/Weka ARFF/XML），转换为 Python/pandas DataFrame，并**支持任意格式双向互转**（SPSS↔Stata↔R↔SAS↔Excel↔Parquet↔HDF5↔JSON…），100% 保留变量标签、值标签等全部元数据。

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

| 格式 | 扩展名 | 依赖 | 变量标签 | 值标签 | 特殊缺失 | 公式 | 元数据保留 |
|-------------|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|
| CDISC ODM | `.odm` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅临床数据 |
| EpiData | `.rec` | R | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过R读入 |
| EpiInfo | `.prj` `.xml` | xml/etree | ✅ | ✅(codes) | ✗ | ✗ | ✅ XML结构 |
| Excel | `.xlsx` `.xls` `.xlsm` | openpyxl / xlrd | ✗ | ✗ | ✗ | ⚠️ 仅结果 | ⚠️ 写出用额外工作表 |
| EViews | `.wf1` `.wf2` | 内置 | ✗ | ✗ | ✗ | ✗ | ⚠️ JSON结构 |
| Feather | `.feather` `.arrow` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 |
| FST | `.fst` | fst (R) | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 |
| GraphPad Prism | `.pzfx` `.pz` | pzfx | ✗ | ✗ | ✗ | ✗ | ⚠️ 多表 |
| Gretl | `.gdt` `.gdtb` | 内置 | ✅ | ✅(tables) | ✗ | ✗ | ✅ string-tables |
| HDF5 | `.h5` `.hdf5` | h5py | ✗ | ✗ | ✗ | ✗ | ⚠️ 层级结构，写出用文件属性 |
| HTML | `.html` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅表格 |
| jamovi | `.omv` | ZIP内置 | ✅ | ✅ | ✗ | ✗ | ✅ JSON分析 |
| JMP | `.jmp` | jmpio-python | ⚠️ | ⚠️ | ✗ | ✗ | ⚠️ 多表 |
| JSON | `.json` | 内置 | ✅ | ✅ | ✗ | ✗ | ✅ 写出嵌入stat-full-meta |
| MATLAB | `.mat` | scipy | ✗ | ✗ | ✗ | ✗ | ⚠️ 变量名 |
| Minitab | `.mtw` `.mpj` | mtbpy / R | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过R读入 |
| ODS | `.ods` | odfpy | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅数据 |
| ORC | `.orc` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 |
| Parquet | `.parquet` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 嵌套类型，写出用schema.metadata |
| R | `.rda` `.rds` | pyreadr + R | ✅ | ✅ | ✅ | ✗ | ✅ statdata_meta，写出通过R桥接 |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | pyreadstat | ✅ | ✅(需catalog) | ⚠️ | ✗ | ✅ |
| SPSS | `.sav` `.zsav` `.por` | pyreadstat | ✅ | ✅ | ✅ | ✗ | ✅ |
| Stata | `.dta` | pyreadstat | ✅ | ✅ | ⚠️ | ✗ | ✅ |
| Weka ARFF | `.arff` | 内置 | ✅ | ✅(nominal) | ✗ | ✗ | ✅ 名义映射 |
| XML | `.xml` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 结构保留 |

> ✅=完整保留 · ⚠️=部分保留或条件性 · ✗=无法保留
*按字母排序*

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

以下仅列出**真正的限制和警告**，默认支持的不重复说明。
*按字母排序，能力矩阵见 SKILL.md。*

### CDISC ODM (.odm)
**读入限制：**
- XML 结构依赖，嵌套解析取决于 ODM 文件结构规范性。复杂的 AttributeValue 结构可能解析不完整。
- ODM 规范本身不含统计元数据（变量标签、值标签），仅保留临床数据结构。

### EpiData (.rec)
**读入限制：**
- 唯一读入路径为 R + `foreign` 包。无 Python 原生备选方案。
- 统计元数据（变量标签、值标签）在 R → CSV 桥接过程中丢失。

### EpiInfo (.prj)
**读入限制：**
- 项目文件不含数据，需关联外部 CSV。
- 自动搜索同名 CSV 或交叉验证目录内 CSV。
- Access 不支持，需先导出 CSV。

### Excel (.xlsx/.xls)
**读入限制：**
- 合并单元格仅保留左上角值，其余为 NaN。
- 公式丢失，仅保留计算结果。
- 图表/形状不提取。

**转存说明：**
- 变量/值标签存储在独立元数据工作表中。

### HDF5 (.h5)
**读入限制：**
- 层级结构展平为顶级变量。
- HDF5 数据集属性收集到 `hdf5_metadata.file_attributes` 中，但不自动解析为变量标签。仅 `stat-full-meta` 格式嵌入元数据可自动恢复。

**转存说明：**
- 写入时使用文件级属性存储元数据（via h5py）。

### JMP (.jmp)
**读入限制：**
- 依赖 jmpio-python，版本支持不一。
- 多表 JMP 文件仅返回第一个数据表（额外表的元数据保存在 jmp_metadata 中）。

**转存说明：**
- 仅支持单表写出，多表结构可能丢失表级元数据。

### MATLAB (.mat)
**读入限制：**
- v7.3+（HDF5 格式）：scipy.io.loadmat 无法读取，当前代码路径中未实现 h5py 回退。
- 复杂结构（嵌套 cell、稀疏矩阵、函数句柄）回退为单列扁平化输出。
- Object 类和 datetime 列在转换中丢失类型保真度。

### Parquet (.parquet)
**读入限制：**
- 深层嵌套类型（>2 层 list<struct>）通过 pyarrow.to_pandas() 转换后变为不透明的 Python 对象列。Arrow schema 保真度保留，但 pandas 表示可能丢失结构。
- 分区数据集暂未支持（仅单文件）。

### R (.rda/.rds)
**读入限制：**
- 旧版 ASCII XDR (RDA2)：pyreadstat 无法读取，**已自动回退到 R**（推荐安装 R）。无 R 时该格式失败。
- factor 顺序可能未保留为 Categorical 顺序，除非通过 stat-full-meta 嵌入。
- 多对象 RDA 文件：`read_all_r_objects()` 返回全部对象列表。

**转存说明：**
- 写回操作通过 R 桥接（statdata_meta 属性）实现完整元数据往返。

### SAS (.sas7bdat)
**读入限制：**
- 值标签定义在 `.sas7bcat`，需与数据文件同目录自动加载。
- Viya CAS 新格式不支持。
- 日期基准：1960-01-01。

### SPSS (.sav/.zsav/.por)
**读入限制：**
- MR Sets 读入为原始字典，语义需手动重建。
- 公式丢失，仅保留计算结果。
- 特殊缺失值标记需保留。
- `.zsav` 读入需 gzip 解压，pyreadstat 1.2+ 直接支持，否则自动降级为解压后读入。
- `.por` 为 SPSS 旧版导出格式，变量类型映射可能简化。

**转存说明：**
- `.zsav` 写出需 pyreadstat 1.2+ 支持，否则自动降级为 `.sav` 写出。

### Stata (.dta)
**读入限制：**
- 特殊缺失值（.a–.z）：当 user_missing=True（默认）时保留为 DataFrame 中的字符标签；当 user_missing=False 时不可逆地变为 NaN。
- 旧版 (pre-v13) 可能 Latin-1 编码，需指定 encoding='latin1'。
- Stata 117-119（最新格式）：pyreadstat 1.3.5 不支持，写回时自动降级为 version 15。

**转存说明：**
- user_missing=True 时特殊缺失标签通过 missing_user_values 参数正确写回。

## 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。
