# statdata-transfer | 统计数据格式转换器

[🇬🇧 English](./README.md)

---

读入 50+ 统计软件及临床试验数据格式（CDISC ODM/EpiData/EpiInfo/Excel/EViews/Feather/FST/GraphPad Prism/Gretl/HDF5/HTML/jamovi/JMP/JSON/MATLAB/Minitab/ODS/ORC/Parquet/R/SAS/SPSS/Stata/Weka ARFF/XML），转换为 Python/pandas DataFrame，并**支持任意格式双向互转**（SPSS↔Stata↔R↔SAS↔Excel↔Parquet↔HDF5↔JSON…）。对统计二进制格式（SPSS/Stata/SAS/R/Excel/Parquet/HDF5…）完整保留变量标签、值标签等元数据；文本格式（CSV/XML/HTML/ODS）与 JSON 仅保留可保留的子集——详见「格式限制」。

注意：本技能不需要任何统计软件的支持，但功能仅限于数据格式转换。如果需要**AI 智能体接入已安装的统计软件进行分析**，请使用 **[statsoft-cli](https://github.com/medstatstar/statsoft-cli)** 技能。

## 核心能力

### 读入（数据提取）
从 50+ 统计软件格式中提取数据 + 元数据，转为 pandas DataFrame，尽可能完整保留元数据，并明确标注保留/丢失情况。

### 转存（格式转换）
- **统计格式互转**：SPSS ↔ Stata ↔ R ↔ SAS XPT（保留全部元数据）
- **导出通用格式**：Parquet、Feather、HDF5、JSON、CSV、TSV、Excel（元数据嵌入 schema.metadata 或 sidecar JSON）
- **通用格式→统计格式**：通过嵌入的 `stat-full-meta` 反向保留元数据

### 自动警告
转换时检测并报告哪些元数据可以保留、哪些会丢失，避免静默的数据损失。所有警告信息均为中英双语。

## 支持格式与能力矩阵

*按字母排序。*

| 格式 | 扩展名 | 依赖 | 变量标签 | 值标签 | 特殊缺失 | 公式 | 元数据保留 |
|------|--------|------|---------|--------|---------|------|-----------|
| CDISC ODM | `.odm` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅临床数据 |
| dBASE / FoxPro | `.dbf` | dbfread / dbf | ✗ | ✗ | ✗ | ✗ | ⚠️ 读+写；大写字段名 |
| EpiData | `.rec` | R foreign | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过 R 读入 |
| EpiInfo | `.prj` `.xml` | xml/etree | ✅ | ✅(codes) | ✗ | ✗ | ✅ XML 结构 |
| Excel | `.xlsx` `.xls` `.xlsm` | openpyxl / xlrd | ✗ | ✗ | ✗ | ⚠️ 仅结果 | ⚠️ 写出用额外工作表；合并单元格填充 |
| EViews | `.wf1` `.wf2` | 内置 | ✗ | ✗ | ✗ | ✗ | ⚠️ JSON 结构 |
| Feather | `.feather` `.arrow` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 |
| FST | `.fst` | fst (R) | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 |
| GraphPad Prism | `.pzfx` `.pz` | pzfx | ✗ | ✗ | ✗ | ✗ | ⚠️ 多表 |
| Gretl | `.gdt` `.gdtb` | 内置 | ✅ | ✅(tables) | ✗ | ✗ | ✅ string-tables |
| HDF5 | `.h5` `.hdf5` | h5py | ✗ | ✗ | ✗ | ✗ | ⚠️ 层级结构 + 属性标签 |
| HTML | `.html` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅表格 |
| jamovi | `.omv` | ZIP 内置 | ✅ | ✅ | ✗ | ✗ | ✅ JSON 分析 |
| JMP | `.jmp` | jmpio-python | ⚠️ | ⚠️ | ✗ | ✗ | ⚠️ 多表 |
| JSON | `.json` | 内置 | ✅ | ✅ | ✗ | ✗ | ✅ 写出嵌入 stat-full-meta |
| MATLAB | `.mat` | scipy | ✗ | ✗ | ✗ | ✗ | ⚠️ v7.3+ 走 h5py 回退 |
| Mathematica | `.wdx` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Best-effort XML |
| Minitab | `.mtw` `.mpj` | mtbpy / R | ✗ | ✗ | ✗ | ✗ | ⚠️ 通过 R 读入 |
| MS Access | `.mdb` `.accdb` | pyodbc + Access 驱动 | ✗ | ✗ | ✗ | ✗ | ⚠️ 多表；需系统驱动 |
| ODS | `.ods` | odfpy | ✗ | ✗ | ✗ | ✗ | ⚠️ 仅数据 |
| ORC | `.orc` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 版本差异 |
| Origin | `.opju` `.oggu` | zipfile + lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ Best-effort |
| Parquet | `.parquet` | pyarrow | ✅(schema) | ✅(schema) | ✗ | ✗ | ⚠️ 嵌套类型；分区数据集 |
| R | `.rda` `.rds` `.rdata` | pyreadr + R | ✅ | ✅ | ✅ | ✗ | ✅ statdata_meta + R 桥接 |
| SAS | `.sas7bdat` `.xpt` `.sas7bcat` | pyreadstat | ✅ | ✅(需 catalog) | ⚠️ | ✗ | ✅ |
| SPSS | `.sav` `.zsav` `.por` | pyreadstat | ✅ | ✅ | ✅ | ✗ | ✅ |
| Stata | `.dta` | pyreadstat | ✅ | ✅ | ⚠️ | ✗ | ✅ |
| Weka ARFF | `.arff` | 内置 | ✅ | ✅(nominal) | ✗ | ✗ | ✅ 名义映射 |
| XML | `.xml` | lxml | ✗ | ✗ | ✗ | ✗ | ⚠️ 结构保留 |

> ✅=完整保留 · ⚠️=部分保留或条件性 · ✗=无法保留

### 探测降级格式
无现成解析库，识别扩展名并给出清晰导出指引（不解析数据）。

| 格式 | 扩展名 | 导出指引 |
|------|--------|---------|
| LIMDEP / NLOGIT | `.lpw` | 从原软件导出 CSV |
| NCSS | `.ncss` | 导出 CSV |
| OxMetrics | `.in7` | 导出 CSV / `.dta` |
| Paradox | `.db` `.px` | 导出 `.dbf` / CSV |
| SAS CPORT | `.cpt` | SAS: `proc export` 为 XPORT(`.xpt`) / `.sas7bdat` |
| Statistica | `.sta` | 导出 `.sav` / `.csv` |
| SYSTAT | `.sys` `.syd` | 导出 CSV / `.sav` |

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
    "column_report": {"q1": {"source_type": "int", "pandas_dtype": "int64"}},
}
```

## 元数据保留层级

### 读入降损规则
1. **统计二进制格式**（SPSS/Stata/SAS/R）：100% 元数据完整保留
2. **Arrow 生态**（Parquet/Feather/ORC/FST）：仅还原 `write_stat_file` 写入的标签
3. **非统计格式**（CSV/Excel/XML/HTML/ODS）：仅保留数据值；可使用 `apply_value_labels()` 手动附加
4. **R 格式**：v1.6.0+ 通过 `statdata_meta` 属性嵌入全部元数据

### 元数据丢失警告
运行时 `warnings` 列表包含：
- 特殊缺失值变为 NaN
- 测量级别/显示宽度/对齐方式丢失
- 多重响应集（MR Sets）无法保留
- 文件标签/注释不保留
- 日期基准不保存

## 提供输入文件 | Providing Input File

AI 智能体（如 WorkBuddy）只能直接上传有限类型的文件。当数据文件无法直接上传时，有两种方式：

1. **在提示词中使用文件绝对路径**（如 `convert C:/Users/Name/Desktop/data.sav to .dta`）
2. **将文件压缩为 `.zip` 包**后上传

技能会自动解压并处理包含单个数据文件的 zip 归档。

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
| pyreadstat (SPSS/Stata/SAS) | 全文件加载到 RAM |
| HDF5 | 支持分块读取；不受 RAM 限制 |
| Parquet | pyarrow 支持 mmap 映射；可处理 >内存的文件 |

## 编码注意事项

- **中文文件**：旧版 Stata/SAS 可能使用 GBK/gb2312。使用 `encoding='gbk'`。
- **欧洲文件**：部分 SAS 文件使用 Latin-1。UTF-8 失败时尝试 `encoding='latin1'`。
- **自动检测**：SPSS/Stata/SAS 默认启用 `_auto_detect_encoding`。

## 快速开始

```bash
# 检查环境
python scripts/check_env.py --install
```

完整代码示例：[`references/usage_examples.py`](./references/usage_examples.py)

WorkBuddy 对话示例：
```
> convert data.sav to .dta
> 读入 data.sav 并显示元数据
> .sav 转 .xlsx 会丢失元数据吗？
```

## 扩展

需要支持新格式？编辑 `scripts/reader_*.py` 添加读入函数，在 `scripts/reader_core.py` 的 `format_map` 中注册，并在 `scripts/reader_core.py` 中补充对应的 TypedDict 定义。

## 格式限制与解决方案

*已解决项标 ✅ / 新增能力标 🔄；未标项为固有格式限制（按字母排序，能力矩阵见上）。*

### CDISC ODM (.odm)
**读入：**
- ❌ XML 结构依赖，嵌套解析取决于 ODM 文件结构规范性
- ❌ ODM 规范本身不含统计元数据，仅保留临床数据结构

### dBASE / FoxPro (.dbf)
**读入：**
- ❌ 字段名强制大写（格式限制）
- ✅ 支持读+写

### EpiData (.rec)
**读入：**
- ❌ 唯一读入路径为 R + `foreign` 包
- ❌ 统计元数据在 R → CSV 桥接过程中丢失

### EpiInfo (.prj)
**读入：**
- ❌ 项目文件不含数据；自动搜索同名 CSV
- ❌ Access 不支持，需先导出 CSV
**写出：**
- ✅ 变量标签和 codes 在 XML 结构中重建

### Excel (.xlsx/.xls/.xlsm)
**读入：**
- ✅ **合并单元格**：用锚点值填充合并区域；通过 `fill_merged_cells=True`（默认）启用，可传 `False` 关闭
- ❌ 公式丢失，仅保留计算结果
- ❌ 图表/形状不提取
**写出：**
- 变量/值标签存储在独立元数据工作表中

### HDF5 (.h5/.hdf5)
**读入：**
- ✅ **多层级数据集**：`pd.read_hdf` 失败时自动回退到 h5py，合并全部顶层数值数据集
- ✅ **属性标签还原**：扫描常用属性键（`label`、`description`、`units`、`ColumnLabel`…）
- ❌ 层级结构仍展平为顶级变量
**写出：**
- 写入时使用文件级属性存储元数据

### JMP (.jmp)
**读入：**
- ❌ 依赖 jmpio-python，版本支持不一
- ❌ 多表 JMP 文件仅返回第一个数据表
**写出：**
- 仅支持单表写出

### MATLAB (.mat)
**读入：**
- ✅ **v7.3+（HDF5 格式）**：检测 `MATLAB 7.3` 文件头或 scipy 失败 → h5py 路径
- ❌ 复杂结构（嵌套 cell、稀疏矩阵、函数句柄）→ 单列扁平化输出
- ❌ Object 类和 datetime 列丢失类型保真度

### Parquet (.parquet)
**读入：**
- ❌ 深层嵌套类型（>2 层 list<struct>）→ 不透明的 Python 对象列
- ✅ **分区数据集**：含 `part-*.parquet` 或 Hive 分区子目录 → `pyarrow.dataset` 合并读取

### R (.rda/.rds/.rdata)
**读入：**
- ✅ 旧版 ASCII XDR (RDA2)：**自动回退到 R**（推荐安装 R）
- ❌ factor 顺序可能未保留为 Categorical 顺序
- ❌ 多对象 RDA 文件：`read_all_r_objects()` 返回全部对象列表
**写出：**
- 通过 R 桥接（statdata_meta 属性）实现完整元数据往返

### SAS (.sas7bdat/.xpt/.sas7bcat)
**读入：**
- ✅ 值标签定义在 `.sas7bcat`，需与数据文件同目录自动加载
- ❌ Viya CAS `.sashdat` 不支持
- 日期基准：1960-01-01

### SPSS (.sav/.zsav/.por)
**读入：**
- ❌ MR Sets 读入为原始字典，语义需手动重建
- ❌ 公式丢失，仅保留计算结果
- ⚠️ 特殊缺失值（`.A`–`.Z`）在 `special_missing` 中标记；写出时需显式保留
**写出：**
- `.zsav` 写出需 pyreadstat 1.2+ 支持，否则自动降级为 `.sav`

### Stata (.dta)
**读入：**
- ⚠️ 特殊缺失值（`.a`–`.z`）：`user_missing=True`（默认）时保留为字符标签；`user_missing=False` 时不可逆地变为 NaN
- ✅ 旧版 (pre-v13) Latin-1 编码已自动检测
- ❌ Stata 117-119：pyreadstat 1.3.5 不支持，写回时自动降级为 version 15

## 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。
