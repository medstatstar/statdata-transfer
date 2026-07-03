"""
端到端测试脚本 - statdata-transfer v1.4.0
测试各种格式的读取功能
"""
import os
import sys
import tempfile
import pandas as pd
import subprocess

# 添加技能路径
SKILL_DIR = r"C:\Users\WintoneFileSrv\.workbuddy\skills\statdata-transfer"
sys.path.insert(0, SKILL_DIR)

# 测试文件路径
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

def test_spss():
    """测试 SPSS .sav 格式"""
    print("\n=== 测试 SPSS .sav 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.sav")
    
    try:
        import pyreadstat
        pyreadstat.write_sav(df, filepath, file_label="测试数据")
        print(f"✓ 创建测试文件: {filepath}")
        
        # 测试读取
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        print(f"  格式: {result['metadata']['file_format']}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_stata():
    """测试 Stata .dta 格式"""
    print("\n=== 测试 Stata .dta 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.dta")
    
    try:
        import pyreadstat
        pyreadstat.write_dta(df, filepath, version=15)
        print(f"✓ 创建测试文件: {filepath}")
        
        # 测试读取
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        print(f"  格式: {result['metadata']['file_format']}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_excel():
    """测试 Excel .xlsx 格式"""
    print("\n=== 测试 Excel .xlsx 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.xlsx")
    
    try:
        df.to_excel(filepath, index=False, sheet_name="Sheet1")
        print(f"✓ 创建测试文件: {filepath}")
        
        # 测试读取
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        print(f"  格式: {result['metadata']['file_format']}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_rdata():
    """测试 R .rda 格式"""
    print("\n=== 测试 R .rda 格式 ===")
    filepath = os.path.join(TEST_DIR, "test.rda")
    
    try:
        # 使用 R 创建测试文件
        r_script = f"""
        df <- data.frame(
          id = c(1,2,3,4,5),
          name = c('Alice', 'Bob', 'Charlie', 'David', 'Eve'),
          age = c(25, 30, 35, 40, 45),
          score = c(85.5, 90.0, 78.5, 92.0, 88.5),
          category = c('A', 'B', 'A', 'C', 'B'),
          stringsAsFactors=FALSE
        )
        save(df, file='{filepath.replace(chr(92), "/")}')
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write(r_script)
            r_script_file = f.name
        
        # 运行 R 脚本
        r_exe = r"C:\Tools\R-4.5.1\bin\x64\Rscript.exe"
        if os.path.exists(r_exe):
            result = subprocess.run([r_exe, r_script_file], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ 创建测试文件: {filepath}")
                
                # 测试读取
                from scripts.reader_core import read_stat_file
                read_result = read_stat_file(filepath)
                print(f"✓ 读取成功: {len(read_result['dataframe'])} 行, {len(read_result['dataframe'].columns)} 列")
                print(f"  格式: {read_result['metadata']['file_format']}")
                return True
            else:
                print(f"✗ R 脚本执行失败: {result.stderr}")
        else:
            print(f"✗ R 未安装: {r_exe}")
            
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    finally:
        if 'r_script_file' in locals():
            os.unlink(r_script_file)

def test_csv():
    """测试 CSV 格式（作为基准）"""
    print("\n=== 测试 CSV 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.csv")
    
    try:
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"✓ 创建测试文件: {filepath}")
        
        # 测试读取
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        print(f"  格式: {result['metadata']['file_format']}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_parquet():
    """测试 Parquet 格式"""
    print("\n=== 测试 Parquet 格式 ===")
    df = create_test_dataframe()
    filepath = os.path.join(TEST_DIR, "test.parquet")
    
    try:
        df.to_parquet(filepath, index=False)
        print(f"✓ 创建测试文件: {filepath}")
        
        # 测试读取
        from scripts.reader_core import read_stat_file
        result = read_stat_file(filepath)
        print(f"✓ 读取成功: {len(result['dataframe'])} 行, {len(result['dataframe'].columns)} 列")
        print(f"  格式: {result['metadata']['file_format']}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("statdata-transfer 端到端测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("SPSS .sav", test_spss()))
    results.append(("Stata .dta", test_stata()))
    results.append(("Excel .xlsx", test_excel()))
    results.append(("R .rda", test_rdata()))
    results.append(("CSV", test_csv()))
    results.append(("Parquet", test_parquet()))
    
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
