@echo off
chcp 65001 >nul
title Netease Music Downloader - Docker Run

echo.
echo ========================================
echo   Netease Music Downloader - Docker Run
echo ========================================
echo.

:: 检查Docker是否安装
docker --version >nul 2>&1
if not %errorlevel% == 0 (
    echo ERROR: Docker is not installed. Please install Docker first.
    echo Download: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: 检查docker-compose是否安装
docker-compose --version >nul 2>&1
if not %errorlevel% == 0 (
    docker compose version >nul 2>&1
    if not %errorlevel% == 0 (
        echo ERROR: docker-compose is not installed. Please install docker-compose first.
        pause
        exit /b 1
    )
)

:: 创建必要的目录
if not exist downloads (
    mkdir downloads
    echo Created downloads directory
)

:: 检查配置文件是否存在，如果不存在则使用示例配置
if not exist config.json (
    echo WARNING: config.json not found, using config.json.example
    copy config.json.example config.json >nul
)

:: 启动服务
echo Starting services...
docker-compose up -d

if %errorlevel% == 0 (
    echo.
    echo ✅ Services started successfully!
    echo.
    echo 📡 Backend API: http://localhost:5000
    echo 🌐 Frontend UI: http://localhost:3000
    echo 📁 Downloads: .\downloads\
    echo.
    echo To stop services:
    echo   docker-stop.bat
    echo.
    echo To view logs:
    echo   docker-compose logs -f
) else (
    echo.
    echo ❌ Failed to start services!
    pause
    exit /b 1
)

pause
