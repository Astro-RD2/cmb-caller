@echo off
cd /d C:\Users\RoyChing\Documents\Python\cmb-caller

echo 當前 Git 狀態:
git status

echo 移除 Src 下不必要的目錄...

:: 使用 PowerShell 來處理目錄清理
powershell -Command "
cd 'C:\Users\RoyChing\Documents\Python\cmb-caller'
$subdirs = Get-ChildItem 'Src' -Directory
foreach ($dir in $subdirs) {
    if ($dir.Name -ne 'cmb-caller' -and $dir.Name -ne 'cmb-caller-frontend') {
        Write-Host '移除目錄: Src/'$dir.Name
        git rm -r ('Src/' + $dir.Name)
    }
}
"

echo 提交變更...
git commit -m "clean: 清理 Src 目錄，只保留 cmb-caller 和 cmb-caller-frontend"

echo 推送到 GitHub...
git push origin main

echo 清理完成！
pause