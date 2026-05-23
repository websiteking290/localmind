@echo off
chcp 65001 >nul
title LocalMind - Python Setup
color 0b

echo ============================================
echo   LocalMind - Python Environment Setup
echo ============================================
echo.

:: Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python is already installed:
    python --version
    echo.
    goto :done
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python3 is already installed:
    python3 --version
    echo.
    goto :done
)

echo ⚠ Python not found. Installing now...
echo.

:: Create temp directory for installer
set "TEMP_DIR=%TEMP%\localmind_python_setup"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Download Python installer (64-bit, latest stable)
echo ⬇ Downloading Python 3.11.9 installer (~27MB)...
set "PYTHON_INSTALLER=%TEMP_DIR%\python-3.11.9-amd64.exe"

:: Use PowerShell to download
echo   Downloading...
powershell -Command "& {$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%PYTHON_INSTALLER%'}"

if not exist "%PYTHON_INSTALLER%" (
    echo ❌ Download failed!
    echo.
    echo Please install Python manually from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✓ Download complete.
echo.

:: Install Python silently
echo 🔧 Installing Python (this may take a minute)...
echo   Please wait...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

if %errorlevel% neq 0 (
    echo ❌ Python installation failed!
    echo.
    pause
    exit /b 1
)

echo ✓ Python installed successfully.
echo.

:: Verify installation
echo 🔍 Verifying installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python installation verification failed!
    echo Please restart this computer and try again.
    pause
    exit /b 1
)

echo ✓ Python is ready:
python --version
echo.

:: Cleanup
rmdir /s /q "%TEMP_DIR%" 2>nul

:done
echo ============================================
echo   Python setup complete!
echo ============================================
echo.
timeout /t 2 >nul
exit /b 0
