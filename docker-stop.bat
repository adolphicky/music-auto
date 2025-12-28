@echo off
chcp 65001 >nul
title Netease Music Downloader - Docker Stop

echo.
echo ========================================
echo   Netease Music Downloader - Docker Stop
echo ========================================
echo.

:: 检查Docker是否安装
docker --version >nul 2>&1
if not %errorlevel% == 0 (
    echo ERROR: Docker is not installed.
    pause
    exit /b 1
)

:: 检查docker-compose是否安装
docker-compose --version >nul 2>&1
if not %errorlevel% == 0 (
    docker compose version >nul 2>&1
    if not %errorlevel% == 0 (
        echo ERROR: docker-compose is not installed.
        pause
        exit /b 1
    )
)

:: 停止服务
echo Stopping services...
docker-compose down

if %errorlevel% == 0 (
    echo.
    echo ✅ Services stopped successfully!
) else (
    echo.
    echo ❌ Failed to stop services!
    pause
    exit /b 1
)

pause
