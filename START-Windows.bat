@echo off
chcp 65001 >nul
title LocalMind AI — Windows Launcher
cls

echo.
echo   ╔═══════════════════════════════════════════════════════════╗
echo   ║              🤖  LOCALMIND AI - WINDOWS LAUNCHER           ║
echo   ╚═══════════════════════════════════════════════════════════╝
echo.

:: ── Paths ─────────────────────────────────────────────────
set "USB_ROOT=%~dp0"
set "SETUP_PY=%USB_ROOT%LocalMind\setup.py"

:: ── Find Python ─────────────────────────────────────────
set "PYTHON="

:: Check bundled Python first
if exist "%USB_ROOT%LocalMind\launcher\python\python.exe" (
    set "PYTHON=%USB_ROOT%LocalMind\launcher\python\python.exe"
    goto :python_found
)

:: Check system python
python --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON=python"
    goto :python_found
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON=python3"
    goto :python_found
)

:: No Python found — try auto-install
:install_python
echo  ⚠ Python 3.9+ is required but not found.
echo.
echo  LocalMind can download and install Python automatically.
echo  ^(Requires internet connection for this one-time setup^)
echo.

set /p CHOICE="Download and install Python now? (Y/n): "
if /I "%CHOICE%"=="n" goto :no_python
if /I "%CHOICE%"=="no" goto :no_python

echo.
echo  📥 Downloading Python installer...
echo  This may take 2-3 minutes. Please wait.
echo.

:: Create temp dir
set "TEMP_DIR=%TEMP%\localmind_python"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Download Python 3.11 embeddable (smaller, no admin needed)
set "PY_ZIP=%TEMP_DIR%\python-3.11.9-embed-amd64.zip"
set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

powershell -NoProfile -Command "& {$p='SilentlyContinue'; Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_ZIP%'}" >nul 2>&1

if not exist "%PY_ZIP%" (
    echo  ❌ Download failed. Please install Python manually:
    echo     https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Extract to USB (so it's bundled for future runs)
echo  📦 Extracting Python to USB...
powershell -NoProfile -Command "Expand-Archive -Path '%PY_ZIP%' -DestinationPath '%USB_ROOT%LocalMind\launcher\python' -Force" >nul 2>&1

if not exist "%USB_ROOT%LocalMind\launcher\python\python.exe" (
    echo  ❌ Extraction failed.
    pause
    exit /b 1
)

:: Need to get pip working with embeddable
:: Download get-pip.py
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP_DIR%\get-pip.py'" >nul 2>&1
if exist "%TEMP_DIR%\get-pip.py" (
    echo  📦 Installing pip...
    "%USB_ROOT%LocalMind\launcher\python\python.exe" "%TEMP_DIR%\get-pip.py" >nul 2>&1
)

:: Cleanup
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

set "PYTHON=%USB_ROOT%LocalMind\launcher\python\python.exe"
echo  ✅ Python installed on USB.
echo.

goto :python_found

:no_python
echo.
echo  Please install Python 3.9+ from https://www.python.org/downloads/
echo  Then double-click this file again.
echo.
pause
exit /b 1

:python_found
echo  ✓ Python ready:
%PYTHON% --version
echo.

:: ── Run Setup ──────────────────────────────────────────
echo  🚀 Starting LocalMind setup...
echo.

if not exist "%SETUP_PY%" (
    echo  ❌ Setup file not found: %SETUP_PY%
    pause
    exit /b 1
)

cd /d "%USB_ROOT%LocalMind"
%PYTHON% "%SETUP_PY%" --auto

if %errorlevel% neq 0 (
    echo.
    echo  ❌ LocalMind encountered an error.
    pause
)

exit /b 0
