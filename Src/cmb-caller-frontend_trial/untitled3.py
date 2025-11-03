import ast
import importlib
import sys

# 定義標準庫模組（部分示例，實際應使用 sys.stdlib_module_names）
STANDARD_LIB = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else {
    'os', 'sys', 'math', 'datetime', 'json', 're', 'random', 'time'
}

def get_imported_modules(file_path):
    """從目標 Python 檔案提取 import 的模組名稱"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    modules.add(name.name.split('.')[0])  # 提取頂層模組名
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # 確保 module 不為 None
                    modules.add(node.module.split('.')[0])  # 提取頂層模組名
        return modules
    except Exception as e:
        print(f"無法解析檔案 {file_path}: {e}")
        return set()

def check_requirements(modules):
    """檢查模組是否已安裝"""
    missing_modules = []
    
    for module in modules:
        # 忽略標準庫
        if module in STANDARD_LIB:
            continue
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    return missing_modules

def main(target_files):
    all_missing = []
    
    # 處理每個目標檔案
    for target_file in target_files:
        print(f"\n檢查檔案：{target_file}")
        # 提取模組
        imported_modules = get_imported_modules(target_file)
        print(f"檢測到的模組：{imported_modules}")
        
        # 檢查缺少的模組
        missing = check_requirements(imported_modules)
        
        if missing:
            print(f"錯誤：{target_file} 缺少以下第三方套件：")
            for mod in missing:
                print(f"- {mod}")
            all_missing.extend(missing)
        else:
            print(f"{target_file} 的所有第三方套件已安裝！")
    
    # 如果有缺少的套件，顯示安裝命令並退出
    if all_missing:
        print("\n請使用以下命令安裝缺少的套件：")
        for mod in set(all_missing):  # 去重複
            print(f"pip install {mod}")
        sys.exit(1)
    else:
        print("\n所有檔案的第三方套件均已安裝！")

if __name__ == "__main__":
    # 從命令列獲取目標檔案
    if len(sys.argv) < 2:
        print("使用方式：python untitled3.py <目標檔案1> <目標檔案2> ...")
        sys.exit(1)
    
    target_files = sys.argv[1:]  # 獲取所有命令列參數（檔案路徑）
    main(target_files)