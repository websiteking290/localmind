@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title LocalMind AI — Starting...

:: ── Paths ────────────────────────────────────────────
set "USB_ROOT=%~dp0"
set "LAUNCHER_DIR=%USB_ROOT%launcher"
set "PYTHON_EXE=%LAUNCHER_DIR%\python\python.exe"
set "LAUNCHER_PY=%LAUNCHER_DIR%\launcher.py"

:: ── Colors ───────────────────────────────────────────
for /F %%a in ('powershell -NoProfile -Command "[char]27"') do set "ESC=%%a"
set "CYAN=!ESC![36m"
set "GREEN=!ESC![32m"
set "YELLOW=!ESC![33m"
set "RED=!ESC![31m"
set "RESET=!ESC![0m"

echo.
echo !CYAN!    _       _       __  __             _   !RESET!
echo !CYAN!   ^| ^|     ^| ^|     ^|  \/  ^|           ^| ^|  !RESET!
echo !CYAN!   ^| ^| ___ ^| ^|_   _^| \  / ^| __ _ _ __ ^| ^|_ !RESET!
echo !CYAN!   ^| ^|/ _ \^| ^| ^| ^| ^| ^|\\/^| ^|/ _` ^| '_ \^| __^|!RESET!
echo !CYAN!   ^| ^| (_) ^| ^| ^|_^| ^| ^|  ^| ^| (_^| ^| ^| ^| ^| ^|_ !RESET!
echo !CYAN!   ^|_^|\___/ ^|_^|\__, ^|_^|  ^|_^|\__,_^|_^| ^|_^|\__^|!RESET!
echo !CYAN!                 __/ ^|                        !RESET!
echo !CYAN!                ^|___/                         !RESET!
echo.
echo !CYAN!══════════════════════════════════════════════════!RESET!
echo   LocalMind AI — Your AI, Offline
echo !CYAN!══════════════════════════════════════════════════!RESET!
echo.

:: ── Check Python ─────────────────────────────────────
if not exist "%PYTHON_EXE%" (
    echo !YELLOW![~] Python not bundled — checking system Python...!RESET!
    python --version >nul 2>&1
    if errorlevel 1 (
        echo !RED![ERROR] Python not found.!RESET!
        echo !DIM!        LocalMind requires Python 3.9+!RESET!
        echo !DIM!        Download: https://python.org/downloads!RESET!
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

:: ── Check Launcher ──────────────────────────────────
if not exist "%LAUNCHER_PY%" (
    echo !RED![ERROR] Launcher not found: %LAUNCHER_PY%!RESET!
    pause
    exit /b 1
)

:: ── Run Launcher ────────────────────────────────────
echo !GREEN![✓] Starting LocalMind...!RESET!
echo.

"%PYTHON_EXE%" "%LAUNCHER_PY%"

if errorlevel 1 (
    echo.
    echo !RED![ERROR] LocalMind encountered an error.!RESET!
    echo !DIM!        Check data/logs/ for details.!RESET!
    pause
)

exit /b 0
