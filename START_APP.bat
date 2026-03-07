@echo off
title TrustGraph Engine - Digital ShramSetu
color 0A

echo ============================================================
echo  TrustGraph Engine - Digital ShramSetu
echo  Empowering 490 Million Informal Workers
echo ============================================================
echo.

REM Check if server is already running
echo [1/3] Checking if server is running...
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server is already running!
    goto :open_browser
)

echo [INFO] Server not running. Starting...
echo.

REM Start the server in a new window
echo [2/3] Starting FastAPI server...
start "TrustGraph Server" cmd /k "python app.py"

REM Wait for server to start
echo [INFO] Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Check if server started successfully
:check_server
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [WAIT] Server starting...
    timeout /t 2 /nobreak >nul
    goto :check_server
)

echo [OK] Server started successfully!
echo.

:open_browser
echo [3/3] Opening UI in browser...
echo.
echo ============================================================
echo  Available URLs:
echo ============================================================
echo  Landing Page: http://localhost:8000
echo  Auth Page:    http://localhost:8000/auth.html
echo  Dashboard:    http://localhost:8000/index.html
echo  API Docs:     http://localhost:8000/docs
echo  Health Check: http://localhost:8000/api/health
echo ============================================================
echo.

REM Open landing page
start http://localhost:8000

echo.
echo [SUCCESS] TrustGraph Engine is running!
echo.
echo Press any key to exit (server will continue running)...
pause >nul
