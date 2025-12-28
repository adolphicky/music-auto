@echo off
chcp 65001 >nul
title Netease Music Downloader - Auto Start

echo.
echo ========================================
echo   Netease Music Downloader - Auto Start
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if not %errorlevel% == 0 (
    echo ERROR: Python not found, please install Python 3.7+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if not %errorlevel% == 0 (
    echo ERROR: Node.js not found, please install Node.js
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo OK: Environment check passed
echo.

:: Activate virtual environment (if exists)
if exist .venv (
    echo Activating Python virtual environment...
    call .venv\Scripts\activate.bat
    echo OK: Virtual environment activated
    echo.
)

:: Install Python dependencies
if exist requirements.txt (
    echo Installing Python dependencies...
    call pip install -r requirements.txt
    if not %errorlevel% == 0 (
        echo WARNING: Python dependencies installation failed, continuing...
    ) else (
        echo OK: Python dependencies installed
    )
    echo.
)

:: Install frontend dependencies
if exist package.json (
    echo Installing frontend dependencies...
    call npm install
    if not %errorlevel% == 0 (
        echo WARNING: Frontend dependencies installation failed, continuing...
    ) else (
        echo OK: Frontend dependencies installed
    )
    echo.
)

:: Create downloads directory
if not exist downloads (
    mkdir downloads
    echo Created downloads directory: downloads
    echo.
)

:: Check config file
if not exist config.json (
    echo WARNING: config.json not found, using default configuration
    echo.
)

:: Start backend service (background)
echo Starting backend service (port: 5000)...
start /B "Netease Music API" python main.py
if %errorlevel% == 0 (
    echo OK: Backend service started
) else (
    echo ERROR: Backend service failed to start
    pause
    exit /b 1
)

:: Wait for backend service to start
echo Waiting for backend service to start (3 seconds)...
timeout /t 3 /nobreak >nul

:: Check if backend service is healthy
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000/health' -UseBasicParsing -TimeoutSec 5; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel% == 0 (
    echo OK: Backend service health check passed
) else (
    echo WARNING: Backend service health check failed, but continuing...
)
echo.

:: Start frontend service (background)
echo Starting frontend service (port: 3000)...
start /B "Netease Music Frontend" npm run dev
if %errorlevel% == 0 (
    echo OK: Frontend service started
) else (
    echo ERROR: Frontend service failed to start
    pause
    exit /b 1
)

:: Wait for frontend service to start
echo Waiting for frontend service to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   Service Information
echo ========================================
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:3000
echo Downloads: downloads
echo.
echo Services are running in background, you can close this window
echo ========================================
echo.

:: Show stop service instructions
echo.
echo To stop services, run stop.bat or close service windows manually
echo.

pause
