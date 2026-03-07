@echo off
cls
echo ==========================================
echo   TrustGraph Engine - Starting...
echo ==========================================
echo.

echo [1/3] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo Error: Python not found!
    pause
    exit /b 1
)

echo.
echo [2/3] Installing dependencies...
pip install -r requirements-prod.txt --quiet

echo.
echo [3/3] Starting server...
echo.
echo ==========================================
echo   Server starting at http://localhost:8000
echo   Press Ctrl+C to stop
echo ==========================================
echo.

python app.py
