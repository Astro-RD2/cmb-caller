@echo off
cd /d C:\Users\RoyChing\Documents\Python\cmb-caller

echo 1. 拉取遠端變更...
git pull origin main

echo 2. 清理 Src 目錄...
git rm -r --cached Src/
git add Src/cmb-caller/
git add Src/cmb-caller-frontend/

echo 3. 提交變更...
git commit -m "clean: 重構 Src 目錄結構"

echo 4. 推送到 GitHub...
git push origin main --force-with-lease

echo 清理完成！
pause