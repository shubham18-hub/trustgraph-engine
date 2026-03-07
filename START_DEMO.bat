@echo off
echo ============================================
echo TrustGraph Engine - Starting Demo Server
echo ============================================
echo.

REM Kill any existing Python processes on port 8080
echo Stopping any existing servers...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

echo.
echo Starting demo server...
echo.

python demo_server.py

pause
