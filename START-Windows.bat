@echo off
chcp 65001 >nul
title LocalMind AI - Windows Launcher
cls

echo.
echo   [===========================================================]
echo   [             LOCALMIND AI - WINDOWS LAUNCHER                ]
echo   [===========================================================]
echo.

set "USB_ROOT=%~dp0"
set "SETUP_PY=%USB_ROOT%LocalMind\setup.py"

echo   USB_ROOT = %USB_ROOT%
echo   SETUP_PY = %SETUP_PY%
echo.

set "PYTHON="

if exist "%USB_ROOT%LocalMind\launcher\python\python.exe" (
    set "PYTHON=%USB_ROOT%LocalMind\launcher\python\python.exe"
    goto :python_found
)

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

echo   WARNING: Python not found on this computer.
echo.
echo   LocalMind can download Python automatically ^(requires internet^).
echo.
echo   If you prefer to install Python manually:
echo     1. Visit https://www.python.org/downloads/
echo     2. Install Python 3.9 or higher
echo     3. Double-click this file again
echo.
set /p CHOICE="Download Python 3.11 automatically now? (Y/n): "
if /I "%CHOICE%"=="n" goto :no_python
if /I "%CHOICE%"=="no" goto :no_python

set "TEMP_DIR=%TEMP%\localmind_python"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

set "PY_ZIP=%TEMP_DIR%\python-3.11.9-embed-amd64.zip"
set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

echo.
echo   Downloading Python... please wait 2-3 minutes...
powershell -NoProfile -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_ZIP%'" 2>nul

if not exist "%PY_ZIP%" (
    echo   ERROR: Download failed.
    echo   Please visit https://www.python.org/downloads/ to install manually.
    pause
    exit /b 1
)

echo   Extracting Python to USB...
powershell -NoProfile -Command "Expand-Archive -Path '%PY_ZIP%' -DestinationPath '%USB_ROOT%LocalMind\launcher\python' -Force"

if not exist "%USB_ROOT%LocalMind\launcher\python\python.exe" (
    echo   ERROR: Extraction failed.
    pause
    exit /b 1
)

set "PYTHON=%USB_ROOT%LocalMind\launcher\python\python.exe"
echo   Python installed successfully.
echo.
goto :python_found

:no_python
echo.
echo   Please install Python 3.9+ from https://www.python.org/downloads/
echo   Then double-click this file again.
echo.
pause
exit /b 1

:python_found
echo   Python ready:
%PYTHON% --version
echo.

echo   Starting LocalMind...
echo.

if not exist "%SETUP_PY%" (
    echo   ERROR: Setup file not found:
    echo   %SETUP_PY%
    pause
    exit /b 1
)

cd /d "%USB_ROOT%LocalMind"
%PYTHON% "%SETUP_PY%" --auto

if %errorlevel% neq 0 (
    echo.
    echo   LocalMind encountered an error.
    pause
)

exit /b 0
