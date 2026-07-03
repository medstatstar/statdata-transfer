"""
环境检测与包安装脚本 | Environment check and package installer
运行方式 | Run: C:\\Tools\\anaconda3\\python.exe scripts/check_env.py
"""

import subprocess
import sys
import importlib

from .reader_core import _bilingual

REQUIRED_PACKAGES = {
    "pandas": "pandas",
    "pyreadstat": "pyreadstat",
    "pyreadr": "pyreadr",
    "openpyxl": "openpyxl",
    "scipy": "scipy",
    "h5py": "h5py",
    "pyarrow": "pyarrow",
    "lxml": "lxml",
    "odfpy": "odfpy",
    "html5lib": "html5lib",
    # v1.4 新增
    "jmpio": "jmpio-python",
    "pzfx": "pzfx",
}

def check_and_install():
    """检测并安装缺失的包"""
    missing = []
    installed = []

    for import_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            mod = importlib.import_module(import_name)
            version = getattr(mod, "__version__", "unknown")
            installed.append(f"  ✅ {import_name} {version}")
        except ImportError:
            missing.append(pip_name)
            installed.append(f"  ❌ {import_name} ({_bilingual('未安装', 'not installed')})")

    print(_bilingual("=== 包状态检测 ===", "=== Package Status Check ==="))
    print("\n".join(installed))

    if missing:
        missing_str = ', '.join(missing)
        print(f"\n{_bilingual(f'=== 自动安装缺失包: {missing_str} ===', f'=== Auto-installing missing packages: {missing_str} ===')}")
        # 使用 conda 或 pip 安装
        for pkg in missing:
            print(f"\n{_bilingual(f'正在安装 {pkg}...', f'Installing {pkg}...')}")
            try:
                # 先尝试 conda（更快，二进制包）
                result = subprocess.run(
                    ["conda", "install", "-y", pkg, "-c", "conda-forge"],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    # 降级到 pip
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode != 0:
                        print(f"  ❌ {_bilingual(f'{pkg} 安装失败', f'{pkg} install failed')}: {result.stderr[:500]}")
                    else:
                        print(f"  ✅ {pip_name} {_bilingual('已通过 pip 安装成功', 'installed via pip successfully')}")
                else:
                    print(f"  ✅ {pip_name} {_bilingual('已通过 conda 安装成功', 'installed via conda successfully')}")
            except Exception as e:
                print(f"  ❌ {_bilingual(f'{pkg} 安装异常', f'{pkg} install error')}: {str(e)[:200]}")
    else:
        print(_bilingual("\n✅ 所有依赖包已就绪", "\n✅ All dependencies are ready"))

if __name__ == "__main__":
    check_and_install()
