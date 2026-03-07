@echo off
echo ============================================
echo TrustGraph Engine - Setup Script
echo ============================================
echo.

echo [1/4] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)
echo.

echo [2/4] Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [3/4] Initializing database...
python -c "from src.database import db; print('Database initialized successfully')"
if %errorlevel% neq 0 (
    echo ERROR: Database initialization failed
    pause
    exit /b 1
)
echo.

echo [4/4] Running health check...
python system_health_check.py
echo.

echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Configure .env file with your API keys
echo 2. Fix AWS Bedrock permissions (see DEPLOYMENT_GUIDE.md)
echo 3. Run: python app.py
echo 4. Open: http://localhost:8000
echo.
pause
