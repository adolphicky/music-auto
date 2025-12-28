@echo off
chcp 65001 >nul
title Netease Music Downloader - Stop Services

echo.
echo ========================================
echo   Netease Music Downloader - Stop Services
echo ========================================
echo.

echo Stopping services...

:: Stop backend service (Python processes)
echo Stopping backend service...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo Backend service stopped
) else (
    echo Backend service not running
)

:: Stop frontend service (Node.js processes)
echo Stopping frontend service...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo Frontend service stopped
) else (
    echo Frontend service not running
)

:: Additional cleanup for specific processes
echo.
echo Additional cleanup...
:: Kill any remaining Python processes with main.py in command line
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /i "main.py" >nul
    if !errorlevel! == 0 (
        taskkill /f /pid %%i >nul 2>&1
        echo Killed Python process PID: %%i
    )
)

:: Kill any remaining Node.js processes with run dev in command line
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo table /nh') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /i "run.*dev" >nul
    if !errorlevel! == 0 (
        taskkill /f /pid %%i >nul 2>&1
        echo Killed Node.js process PID: %%i
    )
)

echo.
echo ========================================
echo   Service stop operation completed
echo ========================================
echo.

timeout /t 2 /nobreak >nul
