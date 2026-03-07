@echo off
echo ==========================================
echo TrustGraph Engine - 5-Minute Demo
echo ==========================================
echo.
echo Starting demo server...
start /B python simple_server.py
timeout /t 3 /nobreak >nul

echo.
echo Running demo...
python demo.py

echo.
echo Demo complete!
pause
