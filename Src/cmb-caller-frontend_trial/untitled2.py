import importlib
import pkg_resources
import sys

# 定義所需的套件和版本（可選）
REQUIRED_PACKAGES = {
    'numpy': '1.21.0',  # 套件名稱和最低版本
    'pandas': '1.3.0',
    'requests': None,   # 不指定版本
}

def check_requirements():
    missing_packages = []
    
    for package, min_version in REQUIRED_PACKAGES.items():
        try:
            # 嘗試導入模組
            importlib.import_module(package)
            
            # 如果需要檢查版本
            if min_version:
                installed_version = pkg_resources.get_distribution(package).version
                if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(min_version):
                    missing_packages.append(f"{package} (需要版本 >= {min_version}, 當前版本: {installed_version})")
        except ImportError:
            missing_packages.append(f"{package} (未安裝)")
        except pkg_resources.DistributionNotFound:
            missing_packages.append(f"{package} (未安裝)")
    
    return missing_packages

def main():
    # 檢查套件
    missing = check_requirements()
    
    if missing:
        print("錯誤：以下套件未安裝或版本不符合要求：")
        for pkg in missing:
            print(f"- {pkg}")
        print("\n請使用以下命令安裝缺少的套件：")
        for pkg in REQUIRED_PACKAGES:
            if any(pkg in m for m in missing):
                version = REQUIRED_PACKAGES[pkg]
                if version:
                    print(f"pip install {pkg}>={version}")
                else:
                    print(f"pip install {pkg}")
        sys.exit(1)  # 終止程式
    else:
        print("所有必要的套件已安裝！")
        # 繼續執行程式
        # 你的主要程式碼放在這裡
        import numpy
        import pandas
        import requests
        print("程式開始執行...")

if __name__ == "__main__":
    main()