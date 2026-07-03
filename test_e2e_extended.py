"""
扩展端到端测试 - 测试更多格式
"""
import os
import sys
import pandas as pd

SKILL_DIR = r"C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer"
sys.path.insert(0, SKILL_DIR)

TEST_DIR = r"C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer\test_data"
os.makedirs(TEST_DIR, exist_ok=True)

def create_test_dataframe():
    """创建测试用的 DataFrame"""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'score': [85.5, 90.0, 78.5, 92.0, 88.5],
        'category': ['A', 'B', 'A', 'C', 'B']
    })

def test_sas_sas7bdat():
    """测试 SAS .sas7bdat 格式"""
    print("\n=== 测试 SAS .sas7bdat 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.sas7bdat")
    
    try:
        import sas7bdat
        with sas7bdat.SAS7BDAT(filepath, mode='w') as writer:
            writer.from_data_frame(df)
        print(f"✓ 创建测试文件: {filepath}")
        
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_matlab():
    """测试 MATLAB .mat 格式"""
    print("\n=== 测试 MATLAB .mat 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.mat")
    
    try:
        from scipy.io import savemat
        savemat(filepath, {'data': df.values}, do_compression=True)
        print(f"✓ 创建测试文件: {filepath}")
        
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_hdf5():
    """测试 HDF5 .h5 格式"""
    print("\n=== 测试 HDF5 .h5 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.h5")
    
    try:
        df.to_hdf(filepath, key='data', mode='w', index=False)
        print(f"✓ 创建测试文件: {filepath}")
        
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_json():
    """测试 JSON 格式"""
    print("\n=== 测试 JSON 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.json")
    
    try:
        df.to_json(filepath, orient='records', force_ascii=False)
        print(f"✓ 创建测试文件: {filepath}")
        
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("statdata-transfer 扩展端到端测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("SAS .sas7bdat", test_sas_sas7bdat()))
    results.append(("MATLAB .mat", test_matlab()))
    results.append(("HDF5 .h5", test_hdf5()))
    results.append(("JSON", test_json()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
