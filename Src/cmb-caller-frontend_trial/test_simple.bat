@echo on
@echo off

:: 設定編碼為UTF-8，避免中文顯示問題
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 設定顏色和標題
title CMB Frontend Test 啟動器
::color 0A
::color 07
color 0F

REM 檢查是否有第一個參數，若無則使用預設值 100
if "%~1"=="" (
    set runCount=20
) else (
    set runCount=%~1
)

echo runCount=%runCount%


:: 設定延遲範圍（可依需求修改）
set t1=0
set t2=1
:: 計算範圍差值
set /a "range=t2 - t1"

:: 顯示程序標題
echo =================================================================
echo               CMB Frontend Test 批次啟動器
echo =================================================================
echo.

:: 檢查必要檔案是否存在
if not exist "CMB_frontend_test_simple.py" (
    echo [錯誤] 找不到 CMB_frontend_test_simple.py 檔案！
    echo [提示] 請確保該檔案在目前目錄下：%CD%
    echo.
    pause
    exit /b 1
)

:: 檢查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python！請確保 Python 已安裝且在 PATH 中。
    echo.
    pause
    exit /b 1
)

:: 顯示啟動資訊
echo [檢查] CMB_frontend_test_simple.py ✓ 存在
python --version | find "Python" && echo [檢查] Python 環境 ✓ 可用
echo [目錄] %CD%
echo.

::color 0A

:: 啟動 %runCount% 個執行個體
echo =================================================================
echo                     開始啟動執行個體
echo =================================================================
echo.

:: 記錄啟動時間
echo [時間] 開始時間：%DATE% %TIME:~0,8%
echo.


for /L %%i in (1,1,%runCount%) do (
    echo [啟動] 正在啟動第 %%i 個執行個體...
    
    :: 使用唯一的視窗標題啟動Python程序
    start "CMB_Instance_%%i" python CMB_frontend_test_simple.py
   
)


echo.
echo =================================================================
echo                   所有執行個體啟動完成
echo =================================================================

:: 顯示目前執行的Python執行個體狀態
echo.
echo [狀態] 目前執行的 Python 執行個體：
tasklist /fi "imagename eq python.exe" /fo table 2>nul | findstr "python.exe"
if errorlevel 1 (
    echo [警告] 未檢測到執行中的 Python 執行個體
) else (
    :: 計算執行個體數量
    for /f %%x in ('tasklist /fi "imagename eq python.exe" ^| find /c "python.exe"') do set count=%%x
    echo.
    echo [資訊] 共偵測到 !count! 個 Python 執行個體正在執行
)

echo.
echo =================================================================
echo                      管理選項
echo =================================================================
echo.
echo 請選擇操作：
echo [1] 保持執行個體運行（關閉此視窗）
echo [2] 一鍵關閉所有執行個體
echo.
set /p choice="請輸入選項 (1 或 2)："

if "%choice%"=="1" (
    echo.
    echo [資訊] 執行個體將繼續在背景運行
    echo [提示] 如需關閉，請重新執行此批次檔並選擇選項 2
    pause
    exit /b 0
)

if "%choice%"=="2" goto SHUTDOWN

echo [錯誤] 無效選項，預設關閉所有執行個體...

:SHUTDOWN
echo.
echo =================================================================
echo                    開始關閉所有執行個體
echo =================================================================
echo.

:: 方法1：透過視窗標題精確關閉我們啟動的執行個體
echo [關閉] 嘗試透過視窗標題關閉執行個體...
set closed_count=0
for /L %%i in (1,1,%runCount%) do (
    echo [嘗試] 第 %%i 個執行個體關閉
    ::tasklist /fi "WINDOWTITLE eq CMB_Instance_%%i*" 2>nul | find "python.exe" >nul
    tasklist /fi "WINDOWTITLE eq CMB_Instance_%%i" 2>nul | find "python.exe" >nul
    if not errorlevel 1 (
        ::taskkill /fi "WINDOWTITLE eq CMB_Instance_%%i*" /f >nul 2>&1
        taskkill /fi "WINDOWTITLE eq CMB_Instance_%%i" /f >nul 2>&1
        if not errorlevel 1 (
            echo [成功] 第 %%i 個執行個體已關閉 ✓
            set /a closed_count+=1
        ) else (
            echo [失敗] 無法關閉第 %%i 個執行個體
        )
    )
)

echo.
rem echo [資訊] 已關閉 %closed_count% 
echo [資訊] 已關閉 !closed_count! 個執行個體


:: 等待2秒讓執行程序完全關閉
echo [等待] 等待執行程序完全關閉...
timeout /t 2 >nul

:: 檢查是否還有Python執行程序在執行
tasklist /fi "imagename eq python.exe" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [偵測] 仍有 Python 執行程序在執行中
    echo [選項] 是否要強制關閉所有 Python 執行程序？(y/N) 
    set /p force_close="輸入 y 確認強制關閉："
    
    if /i "%force_close%"=="y" (
        echo [執行] 強制關閉所有 Python 執行程序...
        taskkill /im python.exe /f >nul 2>&1
        if not errorlevel 1 (
            echo [成功] 所有 Python 執行程序已強制關閉 ✓
        ) else (
            echo [資訊] 沒有找到需要關閉的 Python 執行程序
        )
    ) else (
        echo [略過] 已跳過強制關閉
    )
) else (
    echo [確認] 所有相關執行程序已成功關閉 ✓
)

echo.
echo =================================================================
echo                       執行完成
echo =================================================================
echo.
echo [時間] 結束時間：%DATE% %TIME:~0,8%
echo [狀態] 程序執行完成

echo.
pause
color 0F
