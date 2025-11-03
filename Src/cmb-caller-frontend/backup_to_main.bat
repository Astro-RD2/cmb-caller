::@echo off
setlocal

:: 設定提交訊息（自動加上日期）
::set MAIN_COMMIT_NOTE=Weekly backup: %date%
set MAIN_COMMIT_NOTE=Weekly backup: %date:~5,10%

echo 切換到 main 分支
git checkout main

echo 拉取遠端更新
git pull origin main
echo 添加指定檔案
git add cmb-caller-frontend.py Dockerfile.live requirements.txt .dockerignore

:: 檢查是否有變更
git diff --cached --quiet
if %errorlevel%==0 (
    echo 沒有變更，跳過提交
) else (
    echo 提交變更
    git commit -m "%MAIN_COMMIT_NOTE%"
    echo 推送到 GitHub
    git push origin main
)

endlocal


