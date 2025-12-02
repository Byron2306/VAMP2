@echo off
REM ============================================================================
REM VAMP Agent Backend - Shutdown Script for Windows
REM ============================================================================
REM Gracefully shuts down VAMP backend and associated processes
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "ERROR=[ERROR]"
set "WARNING=[WARNING]"

cls
echo.
echo ============================================================================
echo              VAMP Agent Backend - Shutdown Wizard
echo ============================================================================
echo.

REM ============================================================================
REM Step 1: Find and Kill uvicorn Process
REM ============================================================================
echo %INFO% Shutting down backend server...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO TABLE ^| find "python"') do (
    REM Check if it's our uvicorn process by looking at the process details
    taskkill /PID %%i /F >nul 2>&1
)

REM Alternative: Kill by window title (if backend was started with our script)
taskkill /FI "WINDOWTITLE eq VAMP Backend*" /F >nul 2>&1

echo %SUCCESS% Backend server stopped
echo.

REM ============================================================================
REM Step 2: Close Chrome Extension Page
REM ============================================================================
echo %INFO% Closing Chrome extensions page...
taskkill /FI "WINDOWTITLE eq *chrome*" /F >nul 2>&1
echo %SUCCESS% Browser tabs closed (if applicable)
echo.

REM ============================================================================
REM Step 3: Verify Port 8000 is Free
REM ============================================================================
echo %INFO% Verifying port 8000 is free...
netstat -ano | find ":8000" >nul 2>&1
if %errorlevel% equ 0 (
    echo %WARNING% Port 8000 is still in use
    echo Trying harder to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| find ":8000"') do (
        taskkill /PID %%i /F >nul 2>&1
    )
) else (
    echo %SUCCESS% Port 8000 is now free
)
echo.

REM ============================================================================
REM Final Summary
REM ============================================================================
cls
echo.
echo ============================================================================
echo                   %SUCCESS% SHUTDOWN COMPLETE!
echo ============================================================================
echo.
echo VAMP Agent Backend has been stopped.
echo.
echo What was stopped:
echo   - FastAPI backend server (uvicorn)
echo   - Browser tabs (Chrome extensions page)
echo.
echo To restart VAMP:
echo   - Run: start_vamp.bat
echo.
echo To remove VAMP completely:
echo   - Delete the venv\ folder
echo   - Delete the config\ folder
echo   - Delete the .env file
echo.
echo Troubleshooting:
echo   - If port 8000 is still in use, restart your computer
echo   - Check Windows Task Manager for lingering python.exe processes
echo.
pause
exit /b 0
