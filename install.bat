@echo off
REM SKgate CLI - Installation Script for Windows
REM Автоматическая установка SKgate CLI

echo.
echo ============================================================
echo           SKgate CLI - Installation Script
echo              LLM Token Optimization Gateway
echo ============================================================
echo.

REM Check if running from project directory
if not exist "pyproject.toml" (
    echo [ERROR] pyproject.toml not found!
    echo.
    echo Please run this script from the SKgate project directory:
    echo   cd C:\path\to\squeeze-gateway
    echo   install.bat
    echo.
    pause
    exit /b 1
)

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.10 or higher:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
echo.

REM Check pip
echo [2/5] Checking pip...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip is not available
    echo Installing pip...
    python -m ensurepip --upgrade
)
echo [OK] pip is available
echo.

REM Upgrade pip
echo [3/5] Upgrading pip to latest version...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install package
echo [4/5] Installing SKgate CLI...
echo This may take a minute...
python -m pip install -e . --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation failed!
    echo.
    echo Try manual installation:
    echo   pip install -e .
    echo.
    pause
    exit /b 1
)
echo [OK] SKgate CLI installed successfully
echo.

REM Verify installation
echo [5/5] Verifying installation...
sqz --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] 'sqz' command not found in PATH
    echo.
    echo You may need to restart your terminal/PowerShell
    echo Or add Python Scripts to PATH manually:
    echo   %APPDATA%\Python\Python3X\Scripts
    echo.
) else (
    echo [OK] Installation verified
    sqz --version
)

echo.
echo ============================================================
echo                  Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo   1. Close and reopen your terminal/PowerShell
echo.
echo   2. Initialize configuration:
echo      sqz install
echo.
echo   3. Add your Gemini API key:
echo      sqz keys add mykey YOUR_GEMINI_API_KEY
echo.
echo   4. Start the gateway:
echo      sqz start --daemon
echo.
echo   5. Try interactive chat:
echo      sqz chat
echo.
echo For help:
echo   sqz --help
echo   sqz keys --help
echo.
echo Documentation:
echo   https://github.com/coffe-skelet/Sqgateway
echo.
echo GitHub Pages (live demo):
echo   https://coffe-skelet.github.io/Sqgateway/
echo.
echo ============================================================
echo.

pause
