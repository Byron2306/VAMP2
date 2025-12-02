@echo off
REM ============================================================================
REM VAMP Agent Backend - Launch Script for Windows
REM ============================================================================
REM Starts FastAPI backend, launches browser, and opens Chrome extension page
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
echo               VAMP Agent Backend - Starting System
echo ============================================================================
echo.

REM ============================================================================
REM Step 1: Verify Setup
REM ============================================================================
echo %INFO% Verifying setup...
if not exist "venv" (
    echo %ERROR% Virtual environment not found!
    echo Please run setup_vamp.bat first
    pause
    exit /b 1
)

if not exist ".env" (
    echo %ERROR% Configuration file (.env) not found!
    echo Please run setup_vamp.bat first
    pause
    exit /b 1
)

if not exist "main.py" (
    echo %ERROR% main.py not found!
    echo Make sure you're in the vamp-backend directory
    pause
    exit /b 1
)

echo %SUCCESS% Setup verified
echo.

REM ============================================================================
REM Step 2: Activate Virtual Environment
REM ============================================================================
echo %INFO% Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo %ERROR% Failed to activate virtual environment!
    pause
    exit /b 1
)
echo %SUCCESS% Virtual environment activated
echo.

REM ============================================================================
REM Step 3: Check if Backend is Already Running
REM ============================================================================
echo %INFO% Checking if backend is already running...
netstat -ano | find ":8000" >nul 2>&1
if %errorlevel% equ 0 (
    echo %WARNING% Port 8000 is already in use!
    echo The VAMP backend may already be running.
    echo.
    set /p CONTINUE="Continue anyway? (Y/N): "
    if /i not "!CONTINUE!"=="Y" (
        echo Aborted
        pause
        exit /b 1
    )
    echo.
)

REM ============================================================================
REM Step 4: Start FastAPI Backend
REM ============================================================================
echo %INFO% Starting FastAPI backend...
echo.
echo Backend URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ReDoc: http://localhost:8000/redoc
echo.
echo Keep this window open while using VAMP. Close it to stop the backend.
echo.

start "VAMP Backend" cmd /k "title VAMP Backend - FastAPI & uvicorn && python main.py"

REM ============================================================================
REM Step 5: Wait for Backend Startup
REM ============================================================================
echo %INFO% Waiting for backend to start (3 seconds)...
timeout /t 3 /nobreak >nul
echo %SUCCESS% Backend should now be running
echo.

REM ============================================================================
REM Step 6: Verify Backend is Responsive
REM ============================================================================
echo %INFO% Checking if backend is responsive...
for /f "tokens=*" %%i in ('powershell -Command "$ErrorActionPreference='SilentlyContinue'; try { (curl -Uri 'http://localhost:8000/health' -UseBasicParsing).StatusCode } catch { 0 }" 2^>nul') do set HTTP_STATUS=%%i

if "!HTTP_STATUS!"=="200" (
    echo %SUCCESS% Backend is responding correctly
    echo.
) else (
    echo %WARNING% Backend may still be starting up...
    echo If you see errors, wait a moment and try accessing:
    echo   http://localhost:8000/docs
    echo.
)

REM ============================================================================
REM Step 7: Launch Browser with API Documentation
REM ============================================================================
echo %INFO% Opening API documentation in your browser...
start "" "http://localhost:8000/docs"
timeout /t 2 /nobreak >nul
echo %SUCCESS% Browser opened
echo.

REM ============================================================================
REM Step 8: Open Chrome Extension Management Page
REM ============================================================================
echo %INFO% Opening Chrome extensions page (for loading VAMP extension)...
start "" "chrome://extensions/"
timeout /t 1 /nobreak >nul
echo %SUCCESS% Chrome extensions page opened
echo.

REM ============================================================================
REM Final Instructions
REM ============================================================================
cls
echo.
echo ============================================================================
echo                  %SUCCESS% VAMP AGENT BACKEND RUNNING!
echo ============================================================================
echo.
echo Backend Server: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo ReDoc: http://localhost:8000/redoc
echo.
echo Chrome Extension Status:
echo   - The "Chrome extensions" page should have opened
echo   - Navigate to the chrome_extension\ folder in this directory
echo   - Or manually go to chrome://extensions/
echo   - Enable "Developer mode" (toggle in top-right)
echo   - Click "Load unpacked"
echo   - Select the chrome_extension\ folder
echo.
echo Quick Start:
echo   1. Make sure you're logged into your platforms (Outlook, Google Drive, etc)
echo   2. Click the VAMP extension icon in Chrome
echo   3. Select your date range (start/end month and year)
echo   4. Select platforms to scan
echo   5. Click "Start Scan"
echo   6. Watch real-time updates in the backend terminal
echo.
echo Backend Terminal:
echo   - A new window with the backend server is running
echo   - Keep it open while using VAMP
echo   - Close it when finished
echo.
echo Common URLs:
echo   - API Docs: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/health
echo   - Supported Platforms: http://localhost:8000/api/supported-platforms
echo.
echo For help:
echo   - Check README.md for detailed documentation
echo   - Backend logs appear in the backend window
echo   - Browser console (F12) shows extension errors
echo.
echo ============================================================================
echo.
pause
echo Keeping VAMP running. Close this window to shutdown the backend.
pause
