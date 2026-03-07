@echo off
REM TrustGraph Engine - Restart Demo Server

echo ==========================================
echo TrustGraph - Restarting Demo Server
echo ==========================================
echo.

REM Find and kill existing Python server on port 8080
echo Stopping existing server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
    echo Killing process %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

REM Start new server
echo.
echo Starting demo server...
echo.

REM Try venv Python first, then system Python
if exist "venv\bin\python.exe" (
    start "TrustGraph Demo Server" venv\bin\python.exe demo_server.py
) else if exist "C:\msys64\ucrt64\bin\python.exe" (
    start "TrustGraph Demo Server" C:\msys64\ucrt64\bin\python.exe demo_server.py
) else (
    start "TrustGraph Demo Server" python demo_server.py
)

echo.
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Test server
echo.
echo Testing server...
curl -s http://localhost:8080/api/health >nul 2>&1
if errorlevel 1 (
    echo WARNING: Server may not be responding yet
    echo Wait a few seconds and try: http://localhost:8080
) else (
    echo.
    echo ==========================================
    echo Server Started Successfully!
    echo ==========================================
    echo.
    echo Access at: http://localhost:8080
    echo.
    echo Opening browser...
    start http://localhost:8080
)

echo.
pause
