"""
test_conversion.py - 端到端转换测试
"""
import sys, os
sys.path.insert(0, r'C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer')

import pandas as pd
from scripts.reader_core import read_stat_file, write_stat_file, convert_stat_file

TEST_DIR = r'C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer\test_data'
os.makedirs(TEST_DIR, exist_ok=True)

print("=" * 60)
print("statdata-transfer 端到端转换测试")
print("=" * 60)

# === 1. 创建测试 SPSS 文件 ===
df_orig = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'gender': [1, 2, 1, 2, 1],
    'age': [25, 30, 35, 40, 45],
    'score': [85.5, 90.0, 78.5, 92.0, 88.5],
    'category': ['A', 'B', 'A', 'C', 'B']
})

src_sav = os.path.join(TEST_DIR, 'test_src.sav')
metadata = {
    'file_format': 'spss_sav',
    'file_label': 'test_data_with_labels',
    'variable_labels': {
        'id': 'ID',
        'gender': 'Gender',
        'age': 'Age',
        'score': 'Score',
        'category': 'Category',
    },
    'value_labels': {
        'gender': {1: 'Male', 2: 'Female'},
        'category': {'A': 'Cat A', 'B': 'Cat B', 'C': 'Cat C'},
    },
}
write_stat_file(df_orig, src_sav, metadata)
print(f'OK create SPSS: {src_sav}')

# === 2. 读入 SPSS ===
result = read_stat_file(src_sav)
df_read = result['dataframe']
meta_read = result['metadata']
print(f'OK read SPSS: {len(df_read)} rows, {len(df_read.columns)} cols')

# === 3. 测试转换到各种格式 ===
conversions = [
    ('.dta', 'Stata'),
    ('.sav', 'SPSS'),
    ('.zsav', 'SPSS compressed'),
    ('.xlsx', 'Excel'),
    ('.csv', 'CSV'),
    ('.parquet', 'Parquet'),
    ('.json', 'JSON'),
    ('.feather', 'Feather'),
    ('.hdf5', 'HDF5'),
]

for ext, name in conversions:
    dst = os.path.join(TEST_DIR, f'test_out{ext}')
    try:
        info = convert_stat_file(src_sav, dst, metadata=meta_read)
        print(f'OK convert {name} ({ext}): {info["rows"]} rows, {info["columns"]} cols')
    except Exception as e:
        print(f'FAIL convert {name} ({ext}): {e}')

# === 4. 验证转换后可再次读入 ===
print()
print('--- Re-read test ---')
for ext in ['.dta', '.sav', '.zsav', '.xlsx', '.csv', '.parquet', '.json', '.feather', '.hdf5']:
    dst = os.path.join(TEST_DIR, f'test_out{ext}')
    if os.path.exists(dst):
        try:
            r = read_stat_file(dst)
            n_rows = len(r['dataframe'])
            n_cols = len(r['dataframe'].columns)
            print(f'OK re-read {ext}: {n_rows} rows, {n_cols} cols')
        except Exception as e:
            print(f'FAIL re-read {ext}: {e}')

# === 5. 测试 R 转写 ===
print()
print('--- R conversion test ---')
try:
    dst_rda = os.path.join(TEST_DIR, 'test_out.rda')
    convert_stat_file(src_sav, dst_rda, metadata=meta_read)
    print(f'OK convert R .rda')
    r = read_stat_file(dst_rda)
    print(f'OK re-read R .rda: {len(r["dataframe"])} rows')
except Exception as e:
    print(f'FAIL R conversion: {e}')

# === 6. 验证标签保留 ===
print()
print('--- Label preservation test ---')
# 检查 Stata 的值标签
try:
    dst_dta = os.path.join(TEST_DIR, 'test_out.dta')
    r = read_stat_file(dst_dta)
    vl = r['metadata'].get('value_labels', {})
    if vl:
        print(f'OK Stata preserves value_labels: {list(vl.keys())}')
    else:
        print('WARN Stata does NOT preserve value_labels')
except Exception as e:
    print(f'FAIL Stata label check: {e}')

print()
print('=== All tests complete ===')
