"""
test_roundtrip.py - 标签保留 round-trip 测试
"""
import sys, os
sys.path.insert(0, r'C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer')

import pandas as pd
from scripts.reader_core import read_stat_file, write_stat_file

TEST_DIR = r'C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer\test_data'
os.makedirs(TEST_DIR, exist_ok=True)

print("=" * 60)
print("Round-trip 标签保留测试")
print("=" * 60)

# === 创建带标签的数据 ===
df = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'gender': [1, 2, 1, 2, 1],
    'age': [25, 30, 35, 40, 45],
    'score': [85.5, 90.0, 78.5, 92.0, 88.5],
    'category': ['A', 'B', 'A', 'C', 'B']
})

metadata = {
    'file_format': 'test',
    'variable_labels': {
        'id': 'ID',
        'gender': 'Gender',
        'age': 'Age',
        'score': 'Score',
        'category': 'Category',
    },
    'value_labels': {
        'gender': {1: 'Male', 2: 'Female'},
        'category': {'A': 'Type A', 'B': 'Type B', 'C': 'Type C'},
    },
}

# === Round-trip 转换测试 ===
roundtrip_formats = [
    ('.parquet', 'Parquet'),
    ('.feather', 'Feather'),
    ('.hdf5', 'HDF5'),
    ('.json', 'JSON'),
]

all_pass = True
for ext, name in roundtrip_formats:
    out = os.path.join(TEST_DIR, f'rt_test{ext}')
    try:
        # Write with metadata
        write_stat_file(df, out, metadata)
        
        # Read back
        r = read_stat_file(out)
        read_meta = r['metadata']
        
        # Verify labels
        ok_var = read_meta.get('variable_labels', {}) == metadata['variable_labels']
        ok_val = read_meta.get('value_labels', {}) == metadata['value_labels']
        n_cols = len(r['dataframe'].columns)
        
        if ok_var and ok_val and n_cols == 5:
            print(f'  {name}: labels preserved, {n_cols} cols')
        else:
            all_pass = False
            if not ok_var:
                print(f'  {name}: variable labels mismatch')
                print(f'    expected: {metadata["variable_labels"]}')
                print(f'    actual:   {read_meta.get("variable_labels", {})}')
            if not ok_val:
                print(f'  {name}: value labels mismatch')
                print(f'    expected: {metadata["value_labels"]}')
                print(f'    actual:   {read_meta.get("value_labels", {})}')
            if n_cols != 5:
                print(f'  {name}: column count mismatch (expected 5, got {n_cols})')
    except Exception as e:
        all_pass = False
        print(f'  {name}: FAILED - {e}')

print()
print('=== All round-trip tests complete ===')
