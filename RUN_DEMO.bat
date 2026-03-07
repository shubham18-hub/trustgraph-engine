@echo off
cls
color 0A
echo.
echo ========================================
echo   TrustGraph Engine - Live Demo
echo   Digital ShramSetu for 490M Workers
echo ========================================
echo.
echo Starting backend server...
start /B python simple_server.py
timeout /t 2 /nobreak >nul

echo Starting frontend...
cd frontend
start /B python server.py
cd ..
timeout /t 2 /nobreak >nul

echo.
echo Opening demo in browser...
start http://localhost:3000
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Demo is ready!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo Press any key to run automated demo...
pause >nul

python demo.py

echo.
echo Demo complete! Press any key to exit...
pause >nul
