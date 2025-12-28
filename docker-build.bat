@echo off
chcp 65001 >nul
title Netease Music Downloader - Docker Build

echo.
echo ========================================
echo   Netease Music Downloader - Docker Build
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

:: 构建镜像
echo Building Docker image...
docker-compose build

if %errorlevel% == 0 (
    echo.
    echo ✅ Docker image built successfully!
    echo.
    echo To run the application:
    echo   docker-run.bat
) else (
    echo.
    echo ❌ Docker build failed!
    pause
    exit /b 1
)

pause
