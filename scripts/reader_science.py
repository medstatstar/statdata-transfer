"""
reader_science.py - 科学计算格式（MATLAB/HDF5/Parquet/Feather/ORC/FST）
自动从 stat_reader.py 拆分生成
"""

from __future__ import annotations
import os
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Any

import pandas as pd

from .reader_core import (ColumnInfo, MatlabMeta, Hdf5Meta, ParquetMeta, FeatherMeta, OrcMeta, StatFileResult, _bilingual, _calc_missing_pct, _get_source_type, _parse_value_labels, _build_column_report)


# ============================================================
# 科学计算格式（MATLAB/HDF5/Parquet/Feather/ORC/FST）
# ============================================================

def _extract_full_meta(custom_meta: dict) -> dict:
    """从 custom_meta dict 中提取完整元数据，支持新旧两种格式。
    
    优先解析 stat-full-meta（新格式，17 字段），否则回退到
    stat-var-labels / stat-val-labels 旧格式。
    返回要 merge 到最终 metadata 的 dict。
    """
    full_meta_from_embed = {}
    if "stat-full-meta" in custom_meta:
        try:
            from .reader_core import restore_full_meta
            full_meta_from_embed = restore_full_meta(json.loads(custom_meta["stat-full-meta"]))
        except Exception:
            pass
    elif "stat-var-labels" in custom_meta:
        var_labels = {}
        val_labels = {}
        try:
            var_labels = json.loads(custom_meta["stat-var-labels"])
        except Exception:
            pass
        if "stat-val-labels" in custom_meta:
            try:
                val_raw = json.loads(custom_meta["stat-val-labels"])
                val_labels = _parse_value_labels(val_raw)
            except Exception:
                pass
        if var_labels:
            full_meta_from_embed["variable_labels"] = var_labels
        if val_labels:
            full_meta_from_embed["value_labels"] = val_labels
    return full_meta_from_embed


def _read_matlab(filepath: str, timestamp: str) -> StatFileResult:
    """读入 MATLAB .mat 文件，使用 scipy.io.loadmat。"""
    import scipy.io
    import numpy as np

    warnings_list = [_bilingual("MATLAB 格式不含变量标签、值标签等统计元数据，仅保留原始数据值", "MATLAB format does not contain statistical metadata like variable/value labels, only raw data values")]
    mat_data = scipy.io.loadmat(filepath, struct_as_record=False, squeeze_me=True)
    matlab_metadata: dict[str, Any] = {
        "file_variables": {},
        "mat_file_version": None,
        "mat_file_global_variables": [],
    }

    # Extract metadata from the raw mat dict (excluding __header__, __version__, __globals__)
    data_vars = {}
    for key, value in mat_data.items():
        if key.startswith("__") and key.endswith("__"):
            if key == "__header__":
                if isinstance(value, np.ndarray):
                    matlab_metadata["mat_file_header"] = value.tobytes().decode("utf-8", errors="replace")[:200]
            elif key == "__version__":
                if isinstance(value, np.ndarray):
                    matlab_metadata["mat_file_version"] = value.tobytes().decode("utf-8", errors="replace")
            elif key == "__globals__":
                if isinstance(value, np.ndarray):
                    matlab_metadata["mat_file_global_variables"] = [str(v) for v in value]
            continue
        var_info = {
            "type": type(value).__name__,
            "shape": getattr(value, "shape", None),
        }
        if isinstance(value, np.ndarray):
            var_info["dtype"] = str(value.dtype)
        matlab_metadata["file_variables"][key] = var_info
        data_vars[key] = value

    # Try to construct a DataFrame from numeric/struct arrays
    df = pd.DataFrame()
    struct_vars = {k: v for k, v in data_vars.items()
                   if hasattr(v, 'dtype') and v.dtype.names is not None}

    if struct_vars:
        # Struct array: convert to DataFrame
        first_key = list(struct_vars.keys())[0]
        struct_arr = struct_vars[first_key]
        try:
            df = pd.DataFrame(struct_arr)
            used_var = first_key
        except Exception:
            pass
    else:
        # Try numeric arrays
        numeric_vars = {k: v for k, v in data_vars.items()
                        if isinstance(v, np.ndarray) and v.ndim <= 2 and v.dtype.kind in "iufcb"}
        if numeric_vars:
            try:
                arrays = {}
                for k, arr in numeric_vars.items():
                    if arr.ndim == 1:
                        arrays[k] = arr
                    elif arr.ndim == 2:
                        for col_idx in range(arr.shape[1]):
                            arrays[f"{k}_{col_idx}"] = arr[:, col_idx]
                if arrays:
                    max_len = max(len(a) for a in arrays.values())
                    # Broadcast 1D arrays
                    for k, arr in arrays.items():
                        if len(arr) == 1 and max_len > 1:
                            arrays[k] = np.repeat(arr, max_len)
                    df = pd.DataFrame(arrays)
                    used_var = list(numeric_vars.keys())[0]
            except Exception as e:
                warnings_list.append(_bilingual(f"MAT 文件数值数组转换为 DataFrame 失败: {str(e)[:200]}", f"MAT file numeric array conversion to DataFrame failed: {str(e)[:200]}"))

    if df.empty:
        # Fallback: grab first numeric array as single-column
        for key, value in data_vars.items():
            if isinstance(value, np.ndarray) and value.ndim <= 2:
                try:
                    flat = value.flatten()
                    df = pd.DataFrame({key: flat})
                    used_var = key
                    warnings_list.append(_bilingual(f"MAT 文件结构复杂，仅将变量 '{key}' 展平为单列 DataFrame", f"MAT file has complex structure, flattened variable '{key}' as single-column DataFrame"))
                    break
                except Exception:
                    continue

    if df.empty:
        raise ValueError(_bilingual("MAT 文件无法转换为 DataFrame（可能只包含非数值数据/复杂结构）", "MAT file cannot be converted to DataFrame (may contain only non-numeric data/complex structures)"))

    matlab_metadata["selected_variable"] = used_var
    matlab_metadata["total_variables_in_file"] = len(data_vars)

    if len(struct_vars) > 1 or len(data_vars) - len(struct_vars) > 1:
        warnings_list.append(_bilingual(f"MAT 文件包含 {len(data_vars)} 个变量，已选择 '{used_var}' 构造 DataFrame，其余变量信息保留在 matlab_metadata.file_variables", f"MAT file contains {len(data_vars)} variables, selected '{used_var}' for DataFrame, remaining variable info saved in matlab_metadata.file_variables"))

    column_report: dict[str, ColumnInfo] = {}
    for col in df.columns:
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=None,
            has_value_labels=False,
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None,
            display_width=None,
            storage_width=None,
            measure_level=None,
            alignment=None,
            original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    return {
        "dataframe": df,
        "metadata": MatlabMeta(
            file_format="matlab", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels={}, value_labels={}, special_missing={},
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label={},
            missing_user_values={}, missing_ranges={},
            variable_display_width={}, variable_storage_width={},
            variable_measure={}, variable_alignment={},
            column_names_to_labels={}, mr_sets={}, table_name=None,
            matlab_metadata=matlab_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }






def _read_hdf5(filepath: str, timestamp: str) -> StatFileResult:
    """读入 HDF5 文件（.h5/.hdf5），尝试使用 pd.read_hdf，并提取 stat-full-meta / stat-data-meta 属性"""
    import h5py
    
    warnings_list = []
    hdf5_metadata: dict[str, Any] = {
        "datasets": [],
        "file_attributes": {},
        "groups": [],
        "total_datasets": 0,
        "total_groups": 0,
    }
    
    full_meta_from_embed = {}
    
    def _extract_from_attrs(attrs) -> dict:
        """从 h5py attrs 对象中提取元数据，优先 stat-full-meta"""
        if "stat-full-meta" in attrs:
            try:
                from .reader_core import restore_full_meta
                return restore_full_meta(json.loads(attrs["stat-full-meta"]))
            except Exception:
                pass
        # Fallback to old stat-data-meta
        if "stat-data-meta" in attrs:
            try:
                meta_payload = json.loads(attrs["stat-data-meta"])
                result = {}
                if "variable_labels" in meta_payload:
                    result["variable_labels"] = meta_payload["variable_labels"]
                if "value_labels" in meta_payload:
                    result["value_labels"] = _parse_value_labels(meta_payload["value_labels"])
                return result
            except Exception:
                pass
        return {}
    
    # 先尝试使用 pd.read_hdf
    try:
        df = pd.read_hdf(filepath)
        
        # 获取 h5py 元数据和标签
        with h5py.File(filepath, "r") as f:
            ds_count = 0
            for key in f.keys():
                obj = f[key]
                if isinstance(obj, h5py.Dataset):
                    ds_info = {
                        "path": key,
                        "shape": obj.shape,
                        "dtype": str(obj.dtype),
                    }
                    hdf5_metadata["datasets"].append(ds_info)
                    ds_count += 1
                elif isinstance(obj, h5py.Group):
                    hdf5_metadata["groups"].append(key)
            hdf5_metadata["total_datasets"] = ds_count
            hdf5_metadata["total_groups"] = len(hdf5_metadata["groups"])
            for attr_key, attr_val in f.attrs.items():
                if isinstance(attr_val, bytes):
                    hdf5_metadata["file_attributes"][attr_key] = attr_val.decode("utf-8", errors="replace")[:500]
                else:
                    hdf5_metadata["file_attributes"][attr_key] = str(attr_val)[:500]
            
            # 尝试从根属性读取嵌入的元数据
            full_meta_from_embed = _extract_from_attrs(f.attrs)
            # 如果没有，尝试从 dataset 属性读取
            if not full_meta_from_embed:
                for k in f.keys():
                    obj = f[k]
                    if isinstance(obj, h5py.Dataset):
                        ds_meta = _extract_from_attrs(obj.attrs)
                        if ds_meta:
                            full_meta_from_embed = ds_meta
                            break
        
        var_labels = full_meta_from_embed.get("variable_labels", {})
        val_labels = full_meta_from_embed.get("value_labels", {})
        
        column_report: dict[str, ColumnInfo] = {}
        for col in df.columns:
            column_report[col] = ColumnInfo(
                source_type=_get_source_type(df[col]),
                pandas_dtype=str(df[col].dtype),
                original_label=var_labels.get(col),
                has_value_labels=bool(val_labels.get(col)),
                n_missing=int(df[col].isnull().sum()),
                missing_are_special=False,
                precision_warning=False,
                format_string=None, display_width=None, storage_width=None,
                measure_level=None, alignment=None, original_type=None,
            )
        
        result = {
            "dataframe": df,
            "metadata": Hdf5Meta(
                file_format="hdf5", collected_at=timestamp,
                row_count=df.shape[0], column_count=df.shape[1],
                total_missing_pct=_calc_missing_pct(df),
                variable_labels=var_labels, value_labels=val_labels, special_missing={},
                date_origin=None, file_encoding=None, file_label=None,
                creation_time=None, modification_time=None, notes=[],
                original_variable_types={}, readstat_variable_types={},
                variable_value_labels={}, variable_to_label={},
                missing_user_values={}, missing_ranges={},
                variable_display_width={}, variable_storage_width={},
                variable_measure={}, variable_alignment={},
                column_names_to_labels={}, mr_sets={}, table_name=None,
                hdf5_metadata=hdf5_metadata,
            ),
            "warnings": warnings_list,
            "column_report": column_report,
        }
        # Merge all restored fields (包括 variable_labels, value_labels 等全部 17 个字段)
        result["metadata"].update({k: v for k, v in full_meta_from_embed.items() if v})
        return result
    except Exception as e:
        # 降级到 h5py 遍历模式
        warnings_list.append(_bilingual(f"pd.read_hdf 失败，回退到 h5py 模式: {e}", f"pd.read_hdf failed, falling back to h5py mode: {e}"))
    
        def _collect_datasets(name: str, obj):
            if isinstance(obj, h5py.Dataset):
                ds_info = {"path": name, "shape": obj.shape, "dtype": str(obj.dtype)}
                hdf5_metadata["datasets"].append(ds_info)
            elif isinstance(obj, h5py.Group):
                hdf5_metadata["groups"].append(name)
        
        with h5py.File(filepath, "r") as f:
            for attr_key, attr_val in f.attrs.items():
                if isinstance(attr_val, bytes):
                    hdf5_metadata["file_attributes"][attr_key] = attr_val.decode("utf-8", errors="replace")[:500]
                else:
                    hdf5_metadata["file_attributes"][attr_key] = str(attr_val)[:500]
            
            f.visititems(_collect_datasets)
        
        hdf5_metadata["total_datasets"] = len(hdf5_metadata["datasets"])
        hdf5_metadata["total_groups"] = len(hdf5_metadata["groups"])
        
        if not hdf5_metadata["datasets"]:
            raise ValueError(_bilingual("HDF5 文件不包含任何 Dataset", "HDF5 file contains no Dataset"))
        
        best_ds: dict | None = None
        best_size = -1
        for ds_info in hdf5_metadata["datasets"]:
            if ds_info.get("size", 0) > best_size and len(ds_info.get("shape", [])) <= 2:
                best_ds = ds_info
                best_size = ds_info["size"]
        
        if best_ds is None:
            raise ValueError(_bilingual("HDF5 文件中没有可转换为 DataFrame 的 Dataset", "HDF5 file has no Dataset convertible to DataFrame"))
        
        ds_path = best_ds["path"]
        hdf5_metadata["selected_dataset"] = ds_path
        
        with h5py.File(filepath, "r") as f:
            ds = f[ds_path]
            data = ds[:]
            ds_shape = ds.shape
            ds_dtype = ds.dtype
            
            # 尝试读取嵌入的标签（先从根属性，再从 dataset 属性）
            full_meta_from_embed = _extract_from_attrs(f.attrs)
            if not full_meta_from_embed:
                full_meta_from_embed = _extract_from_attrs(ds.attrs)
            
            if len(ds_shape) == 1:
                col_name = ds_path.rsplit("/", 1)[-1] if "/" in ds_path else ds_path
                df = pd.DataFrame({col_name: data})
            elif len(ds_shape) == 2:
                if ds_dtype.names:
                    df = pd.DataFrame(data)
                    df.columns = list(ds_dtype.names)
                else:
                    df = pd.DataFrame(data)
        
        var_labels = full_meta_from_embed.get("variable_labels", {})
        val_labels = full_meta_from_embed.get("value_labels", {})
        
        column_report: dict[str, ColumnInfo] = {}
        for col in df.columns:
            column_report[col] = ColumnInfo(
                source_type=_get_source_type(df[col]),
                pandas_dtype=str(df[col].dtype),
                original_label=var_labels.get(col),
                has_value_labels=bool(val_labels.get(col)),
                n_missing=int(df[col].isnull().sum()),
                missing_are_special=False,
                precision_warning=False,
                format_string=None, display_width=None, storage_width=None,
                measure_level=None, alignment=None, original_type=None,
            )
        
        result = {
            "dataframe": df,
            "metadata": Hdf5Meta(
                file_format="hdf5", collected_at=timestamp,
                row_count=df.shape[0], column_count=df.shape[1],
                total_missing_pct=_calc_missing_pct(df),
                variable_labels=var_labels, value_labels=val_labels, special_missing={},
                date_origin=None, file_encoding=None, file_label=None,
                creation_time=None, modification_time=None, notes=[],
                original_variable_types={}, readstat_variable_types={},
                variable_value_labels={}, variable_to_label={},
                missing_user_values={}, missing_ranges={},
                variable_display_width={}, variable_storage_width={},
                variable_measure={}, variable_alignment={},
                column_names_to_labels={}, mr_sets={}, table_name=None,
                hdf5_metadata=hdf5_metadata,
            ),
            "warnings": warnings_list,
            "column_report": column_report,
        }
        # Merge all restored fields (包括 variable_labels, value_labels 等全部 17 个字段)
        result["metadata"].update({k: v for k, v in full_meta_from_embed.items() if v})
        return result



def _read_parquet(filepath: str, timestamp: str) -> StatFileResult:
    """读入 Parquet 文件，使用 pyarrow.parquet.read_table。"""
    import pyarrow.parquet as pq
    
    warnings_list = []
    parquet_metadata: dict[str, Any] = {}

    pf = pq.ParquetFile(filepath)
    meta = pf.metadata
    parquet_metadata["num_row_groups"] = meta.num_row_groups
    parquet_metadata["num_columns"] = meta.num_columns
    parquet_metadata["num_rows"] = meta.num_rows
    parquet_metadata["serialized_size"] = meta.serialized_size
    parquet_metadata["created_by"] = meta.created_by

    # Schema info
    schema = pf.schema_arrow
    parquet_metadata["schema"] = str(schema)

    # Row groups info
    rg_info_list = []
    for i in range(meta.num_row_groups):
        rg = meta.row_group(i)
        rg_info = {
            "num_rows": rg.num_rows,
            "num_columns": rg.num_columns,
            "total_byte_size": rg.total_byte_size,
        }
        # total_compressed_size 可能在某些 pyarrow 版本中不存在
        if hasattr(rg, 'total_compressed_size'):
            rg_info["total_compressed_size"] = rg.total_compressed_size
        rg_info_list.append(rg_info)
    parquet_metadata["row_groups"] = rg_info_list

    # Column info
    col_info_list = []
    for col_name in schema.names:
        col_field = schema.field(col_name)
        col_info = {
            "name": col_name,
            "type": str(col_field.type),
            "nullable": col_field.nullable,
        }
        col_info_list.append(col_info)
    parquet_metadata["columns_info"] = col_info_list

    # Read the table
    table = pq.read_table(filepath)
    df = table.to_pandas()

    # Custom metadata if any (支持新 stat-full-meta / 旧 stat-var/val-labels)
    full_meta_from_embed = {}
    if hasattr(meta, 'metadata') and meta.metadata:
        custom_meta = {}
        for k, v in meta.metadata.items():
            try:
                key_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                val_str = v.decode("utf-8") if isinstance(v, bytes) else str(v)
            except Exception:
                continue
            custom_meta[key_str] = val_str
        if custom_meta:
            parquet_metadata["custom_metadata"] = custom_meta
            full_meta_from_embed = _extract_full_meta(custom_meta)

    if df.empty:
        warnings_list.append(_bilingual("Parquet 文件解析结果为空", "Parquet file parsed result is empty"))

    column_report: dict[str, ColumnInfo] = {}
    var_labels = full_meta_from_embed.get("variable_labels", {})
    val_labels = full_meta_from_embed.get("value_labels", {})
    for col in df.columns:
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=var_labels.get(col),
            has_value_labels=bool(val_labels.get(col)),
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None,
            display_width=None,
            storage_width=None,
            measure_level=None,
            alignment=None,
            original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True

    result = {
        "dataframe": df,
        "metadata": ParquetMeta(
            file_format="parquet", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels=var_labels, value_labels=val_labels, special_missing={},
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label={},
            missing_user_values={}, missing_ranges={},
            variable_display_width={}, variable_storage_width={},
            variable_measure={}, variable_alignment={},
            column_names_to_labels={}, mr_sets={}, table_name=None,
            parquet_metadata=parquet_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }
    # Merge all restored fields (包括 variable_labels, value_labels 等全部 17 个字段)
    result["metadata"].update({k: v for k, v in full_meta_from_embed.items() if v})
    return result



def _read_feather(filepath: str, timestamp: str) -> StatFileResult:
    """读入 Feather 文件（.feather/.arrow），使用 pyarrow.feather.read_table。
    支持从 schema.metadata 中提取变量标签和值标签。"""
    import pyarrow.feather as ft
    
    warnings_list = []
    feather_metadata: dict[str, Any] = {}
    
    # Read the table
    table = ft.read_table(filepath)
    df = table.to_pandas()
    
    # Metadata from the table
    schema = table.schema
    feather_metadata["schema"] = str(schema)
    feather_metadata["num_rows"] = table.num_rows
    feather_metadata["num_columns"] = table.num_columns
    
    # Column info
    col_info_list = []
    for col_name in schema.names:
        col_field = schema.field(col_name)
        col_info = {
            "name": col_name,
            "type": str(col_field.type),
            "nullable": col_field.nullable,
        }
        col_info_list.append(col_info)
    feather_metadata["columns_info"] = col_info_list
    
    # Custom metadata from table metadata (pyarrow API compatibility)
    full_meta_from_embed = {}
    custom_meta = {}
    if hasattr(table.schema, 'metadata') and table.schema.metadata:
        for k, v in table.schema.metadata.items():
            try:
                key_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                val_str = v.decode("utf-8") if isinstance(v, bytes) else str(v)
                custom_meta[key_str] = val_str
            except Exception:
                pass
        full_meta_from_embed = _extract_full_meta(custom_meta)

    if custom_meta:
        feather_metadata["custom_metadata"] = custom_meta

    column_report: dict[str, ColumnInfo] = {}
    var_labels = full_meta_from_embed.get("variable_labels", {})
    val_labels = full_meta_from_embed.get("value_labels", {})
    for col in df.columns:
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=var_labels.get(col),
            has_value_labels=bool(val_labels.get(col)),
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None,
            display_width=None,
            storage_width=None,
            measure_level=None,
            alignment=None,
            original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    result = {
        "dataframe": df,
        "metadata": FeatherMeta(
            file_format="feather", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels=var_labels, value_labels=val_labels, special_missing={},
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label={},
            missing_user_values={}, missing_ranges={},
            variable_display_width={}, variable_storage_width={},
            variable_measure={}, variable_alignment={},
            column_names_to_labels={}, mr_sets={}, table_name=None,
            feather_metadata=feather_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }
    # Merge all restored fields (包括 variable_labels, value_labels 等全部 17 个字段)
    result["metadata"].update({k: v for k, v in full_meta_from_embed.items() if v})
    return result



def _read_orc(filepath: str, timestamp: str) -> StatFileResult:
    """读入 ORC 文件，使用 pyarrow.orc.read_table。"""
    import pyarrow.orc as orc_reader

    warnings_list = []
    orc_metadata: dict[str, Any] = {}

    # Read the table
    table = orc_reader.read_table(filepath)
    df = table.to_pandas()

    schema = table.schema
    orc_metadata["schema"] = str(schema)
    orc_metadata["num_rows"] = table.num_rows
    orc_metadata["num_columns"] = table.num_columns

    # Column info
    col_info_list = []
    for col_name in schema.names:
        col_field = schema.field(col_name)
        col_info = {
            "name": col_name,
            "type": str(col_field.type),
            "nullable": col_field.nullable,
        }
        col_info_list.append(col_info)
    orc_metadata["columns_info"] = col_info_list

    # Custom metadata (支持新 stat-full-meta / 旧 stat-var/val-labels)
    full_meta_from_embed = {}
    if hasattr(table, "metadata") and table.metadata:
        custom_meta = {}
        for k, v in table.metadata.items():
            try:
                custom_meta[k.decode("utf-8")] = v.decode("utf-8")
            except Exception:
                try:
                    custom_meta[str(k)] = str(v)
                except Exception:
                    pass
        if custom_meta:
            orc_metadata["custom_metadata"] = custom_meta
            full_meta_from_embed = _extract_full_meta(custom_meta)

    column_report: dict[str, ColumnInfo] = {}
    var_labels = full_meta_from_embed.get("variable_labels", {})
    val_labels = full_meta_from_embed.get("value_labels", {})
    for col in df.columns:
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=var_labels.get(col),
            has_value_labels=bool(val_labels.get(col)),
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None, display_width=None, storage_width=None,
            measure_level=None, alignment=None, original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    result = {
        "dataframe": df,
        "metadata": OrcMeta(
            file_format="orc", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels=var_labels, value_labels=val_labels, special_missing={},
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label={},
            missing_user_values={}, missing_ranges={},
            variable_display_width={}, variable_storage_width={},
            variable_measure={}, variable_alignment={},
            column_names_to_labels={}, mr_sets={}, table_name=None,
            orc_metadata=orc_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }
    # Merge all restored fields (包括 variable_labels, value_labels 等全部 17 个字段)
    result["metadata"].update({k: v for k, v in full_meta_from_embed.items() if v})
    return result



def _read_fst(filepath: str, timestamp: str) -> StatFileResult:
    """读入 FST 文件（R fst 包生成，底层为 feather/Arrow IPC 格式），使用 pyarrow.feather.read_table。"""
    import pyarrow.feather as ft

    warnings_list = []
    fst_metadata: dict[str, Any] = {}

    # FST files from R's fst package are Arrow IPC/Feather format
    table = ft.read_table(filepath)
    df = table.to_pandas()

    schema = table.schema
    fst_metadata["schema"] = str(schema)
    fst_metadata["num_rows"] = table.num_rows
    fst_metadata["num_columns"] = table.num_columns

    # Column info
    col_info_list = []
    for col_name in schema.names:
        col_field = schema.field(col_name)
        col_info = {
            "name": col_name,
            "type": str(col_field.type),
            "nullable": col_field.nullable,
        }
        col_info_list.append(col_info)
    fst_metadata["columns_info"] = col_info_list

    # Custom metadata (支持新 stat-full-meta / 旧 stat-var/val-labels)
    full_meta_from_embed = {}
    if hasattr(table, "metadata") and table.metadata:
        custom_meta = {}
        for k, v in table.metadata.items():
            try:
                custom_meta[k.decode("utf-8")] = v.decode("utf-8")
            except Exception:
                try:
                    custom_meta[str(k)] = str(v)
                except Exception:
                    pass
        if custom_meta:
            fst_metadata["custom_metadata"] = custom_meta
            full_meta_from_embed = _extract_full_meta(custom_meta)

    column_report: dict[str, ColumnInfo] = {}
    var_labels = full_meta_from_embed.get("variable_labels", {})
    val_labels = full_meta_from_embed.get("value_labels", {})
    for col in df.columns:
        column_report[col] = ColumnInfo(
            source_type=_get_source_type(df[col]),
            pandas_dtype=str(df[col].dtype),
            original_label=var_labels.get(col),
            has_value_labels=bool(val_labels.get(col)),
            n_missing=int(df[col].isnull().sum()),
            missing_are_special=False,
            precision_warning=False,
            format_string=None, display_width=None, storage_width=None,
            measure_level=None, alignment=None, original_type=None,
        )
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]):
            max_val = df[col].abs().max()
            if pd.notna(max_val) and max_val > 1e15:
                column_report[col]["precision_warning"] = True
                warnings_list.append(f"列 '{col}' 包含 >1e15 的数值，float64 精度可能不足 | Column '{col}' contains values >1e15, float64 precision may be insufficient")

    result = {
        "dataframe": df,
        "metadata": FstMeta(
            file_format="fst", collected_at=timestamp,
            row_count=df.shape[0], column_count=df.shape[1],
            total_missing_pct=_calc_missing_pct(df),
            variable_labels=var_labels, value_labels=val_labels, special_missing={},
            date_origin=None, file_encoding=None, file_label=None,
            creation_time=None, modification_time=None, notes=[],
            original_variable_types={}, readstat_variable_types={},
            variable_value_labels={}, variable_to_label={},
            missing_user_values={}, missing_ranges={},
            variable_display_width={}, variable_storage_width={},
            variable_measure={}, variable_alignment={},
            column_names_to_labels={}, mr_sets={}, table_name=None,
            fst_metadata=fst_metadata,
        ),
        "warnings": warnings_list,
        "column_report": column_report,
    }
    # Merge all restored fields (包括 variable_labels, value_labels 等全部 17 个字段)
    result["metadata"].update({k: v for k, v in full_meta_from_embed.items() if v})
    return result


