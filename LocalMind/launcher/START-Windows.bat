@echo off
chcp 65001 >nul
title LocalMind AI - Starting...
color 0b
cls

echo.
echo   ╔═══════════════════════════════════════════════════════════╗
echo   ║                                                           ║
echo   ║              🤖  LOCALMIND AI - USB LAUNCHER               ║
echo   ║                                                           ║
echo   ║      Run AI models completely offline - No internet       ║
echo   ║                                                           ║
echo   ╚═══════════════════════════════════════════════════════════╝
echo.

:: Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠ Python is not installed on this computer.
        echo.
        echo Press any key to install Python automatically...
        pause >nul
        echo.
        
        :: Run Python installer
        call "%~dp0install-python.bat"
        if %errorlevel% neq 0 (
            echo ❌ Python setup failed.
            echo.
            pause
            exit /b 1
        )
        echo.
    )
)

echo ✓ Python is ready:
python --version 2>&1 || python3 --version 2>&1
echo.

:: Find USB drive letter
set "USB_DRIVE=%~d0"
echo 📍 USB Drive: %USB_DRIVE%
echo.

:: Set paths
set "USB_ROOT=%USB_DRIVE%\LocalMind"
set "OLLAMA_PATH=%USB_ROOT%\ollama\windows"
set "MODELS_PATH=%USB_ROOT%\models"
set "DASHBOARD_PATH=%USB_ROOT%\dashboard"
set "DATA_PATH=%USB_ROOT%\data"
set "OLLAMA_HOST=127.0.0.1:11434"
set "DASHBOARD_HOST=127.0.0.1:3000"

echo 🔧 Setting up environment...
echo.

:: Create data directory if not exists
if not exist "%DATA_PATH%" mkdir "%DATA_PATH%"

:: Start Ollama Server
echo 🚀 Starting Ollama AI Engine...
echo    Server will run at http://%OLLAMA_HOST%
echo.

:: Kill any existing Ollama processes
taskkill /f /im ollama.exe >nul 2>&1
timeout /t 2 >nul

:: Start Ollama in background
start "LocalMind - Ollama Server" /min cmd /c "cd /d "%OLLAMA_PATH%" && set OLLAMA_MODELS=%MODELS_PATH% && set OLLAMA_HOST=%OLLAMA_HOST% && set OLLAMA_ORIGINS=* && ollama.exe serve 2>&1"
timeout /t 3 >nul

:: Verify Ollama is running
curl -s http://%OLLAMA_HOST%/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Ollama server starting up, waiting...
    timeout /t 5 >nul
)

echo ✓ Ollama is running
echo.

:: Start Dashboard
echo 🌐 Starting Dashboard Server...
echo    Dashboard will be available at http://%DASHBOARD_HOST%
echo.

:: Kill any existing dashboard processes
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
timeout /t 2 >nul

:: Start dashboard in background
start "LocalMind - Dashboard" /min cmd /c "cd /d "%DASHBOARD_PATH%" && set OLLAMA_HOST=%OLLAMA_HOST% && set DASHBOARD_HOST=%DASHBOARD_HOST% && set USB_ROOT=%USB_ROOT% && python server.py 2>&1"
timeout /t 3 >nul

:: Open browser
echo 🌍 Opening browser...
start http://%DASHBOARD_HOST%

echo.
echo ═══════════════════════════════════════════════════════════
echo   ✅ LocalMind is running!
echo.
echo   📊 Dashboard:  http://%DASHBOARD_HOST%
echo   🤖 Ollama API: http://%OLLAMA_HOST%
echo.
echo   Press any key to stop LocalMind...
echo ═══════════════════════════════════════════════════════════
echo.

pause >nul

:: Shutdown
echo.
echo 🛑 Shutting down LocalMind...
taskkill /f /im ollama.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo ✓ LocalMind stopped.
echo.
timeout /t 2 >nul
exit /b 0