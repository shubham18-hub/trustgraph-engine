@echo off
echo Installing aiohttp...
echo.

REM Try different methods to install aiohttp

echo Method 1: Using python -m pip
python -m pip install aiohttp
if %errorlevel% equ 0 (
    echo Success! aiohttp installed.
    goto :success
)

echo.
echo Method 2: Using pip directly
pip install aiohttp
if %errorlevel% equ 0 (
    echo Success! aiohttp installed.
    goto :success
)

echo.
echo Method 3: Using py launcher
py -m pip install aiohttp
if %errorlevel% equ 0 (
    echo Success! aiohttp installed.
    goto :success
)

echo.
echo ERROR: Could not install aiohttp
echo.
echo Please try manually:
echo 1. Open Command Prompt as Administrator
echo 2. Run: python -m pip install aiohttp
echo.
pause
exit /b 1

:success
echo.
echo ============================================
echo aiohttp installed successfully!
echo ============================================
echo.
echo You can now run:
echo   python app.py
echo.
pause
