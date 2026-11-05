@echo off
REM Installation script for Squeeze Gateway CLI (Windows)

echo ==================================
echo Squeeze Gateway CLI - Installation
echo ==================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed
    echo Please install Python 3.10 or higher from python.org
    exit /b 1
)

echo Python found
python --version
echo.

REM Check pip
where pip >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip is not installed
    exit /b 1
)

echo pip is available
echo.

REM Install package
echo Installing Squeeze Gateway...
if exist "pyproject.toml" (
    REM Install from source
    pip install -e .
) else (
    REM Install from PyPI
    pip install squeeze-gateway
)

echo.
echo Installation complete!
echo.
echo Next steps:
echo   1. Initialize configuration:
echo      sqz install
echo.
echo   2. Set your Gemini API key:
echo      sqz config set api_key YOUR_API_KEY
echo.
echo   3. Start the gateway:
echo      sqz start
echo.
echo   4. Try interactive chat:
echo      sqz chat
echo.
echo For help: sqz --help
echo Documentation: https://github.com/kirill-skoch/squeeze-gateway
echo.

pause
