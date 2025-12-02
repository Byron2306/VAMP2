@echo off
REM ============================================================================
REM VAMP Agent Backend - Setup Script for Windows
REM ============================================================================
REM One-time setup: Python, venv, dependencies, encryption key, database
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Define colors using character codes (if available)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "ERROR=[ERROR]"
set "WARNING=[WARNING]"

cls
echo.
echo ============================================================================
echo           VAMP Agent Backend - Setup Wizard for Windows
echo ============================================================================
echo.

REM ============================================================================
REM Step 1: Check Python Installation
REM ============================================================================
echo %INFO% Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo %SUCCESS% Found: !PYTHON_VERSION!
echo.

REM ============================================================================
REM Step 2: Create Virtual Environment
REM ============================================================================
echo %INFO% Setting up virtual environment...
if exist "venv" (
    echo %WARNING% Virtual environment already exists, skipping creation...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %ERROR% Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo %SUCCESS% Virtual environment created
)
echo.

REM ============================================================================
REM Step 3: Activate Virtual Environment
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
REM Step 4: Install Python Dependencies
REM ============================================================================
echo %INFO% Installing Python dependencies (this may take a few minutes)...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo %ERROR% Failed to install dependencies!
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo %SUCCESS% Dependencies installed
echo.

REM ============================================================================
REM Step 5: Install Playwright (for eFundi connector)
REM ============================================================================
echo %INFO% Installing Playwright and browser drivers...
pip install playwright >nul 2>&1
playwright install chromium
if %errorlevel% neq 0 (
    echo %WARNING% Playwright installation had issues but VAMP may still work
)
echo %SUCCESS% Playwright configured
echo.

REM ============================================================================
REM Step 6: Create Directories
REM ============================================================================
echo %INFO% Creating required directories...
if not exist "config" mkdir config
if not exist "logs" mkdir logs
if not exist "chrome_extension" mkdir chrome_extension
echo %SUCCESS% Directories created
echo.

REM ============================================================================
REM Step 7: Generate Encryption Key
REM ============================================================================
echo %INFO% Generating encryption key...
if not exist ".env" (
    python -c "from cryptography.fernet import Fernet; key = Fernet.generate_key().decode(); print(key)" > .env.key.tmp
    if !errorlevel! neq 0 (
        echo %ERROR% Failed to generate encryption key!
        pause
        exit /b 1
    )
    
    set /p ENCRYPTION_KEY=<.env.key.tmp
    del .env.key.tmp
    
    echo %SUCCESS% Encryption key generated: !ENCRYPTION_KEY!
    echo.
    
    REM Create .env file
    echo %INFO% Creating .env configuration file...
    (
        echo VAMP_ENCRYPTION_KEY=!ENCRYPTION_KEY!
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo DEBUG=False
        echo SESSION_TIMEOUT=3600
        echo CONNECTOR_TIMEOUT=30
        echo MAX_RETRIES=3
        echo WS_HEARTBEAT_INTERVAL=30
        echo LOG_LEVEL=INFO
    ) > .env
    
    echo %SUCCESS% .env file created
    echo.
) else (
    echo %WARNING% .env already exists, skipping creation
    echo.
)

REM ============================================================================
REM Step 8: Verify Installation
REM ============================================================================
echo %INFO% Verifying installation...
python -c "import fastapi; import pydantic; import cryptography; import aiohttp" >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Some dependencies failed to load!
    pause
    exit /b 1
)
echo %SUCCESS% All dependencies verified
echo.

REM ============================================================================
REM Step 9: Create Chrome Extension Structure (optional)
REM ============================================================================
if not exist "chrome_extension\manifest.json" (
    echo %INFO% Chrome extension files not found, please copy manifest.json, popup.html, and popup.js to chrome_extension\
)
echo.

REM ============================================================================
REM Final Summary
REM ============================================================================
cls
echo.
echo ============================================================================
echo                    %SUCCESS% SETUP COMPLETE!
echo ============================================================================
echo.
echo Your VAMP Agent Backend is ready to launch!
echo.
echo Next steps:
echo   1. Run: start_vamp.bat     (to start the system)
echo   2. Open: http://localhost:8000/docs (to see API documentation)
echo   3. Load Chrome extension from: chrome://extensions/
echo.
echo Configuration saved to: .env
echo Virtual environment: venv\
echo.
echo Troubleshooting:
echo   - If any step fails, check the error message above
echo   - Make sure Python 3.8+ is installed
echo   - For more help, see README.md
echo.
pause
exit /b 0
