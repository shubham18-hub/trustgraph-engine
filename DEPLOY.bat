@echo off
cls
echo ==========================================
echo   TrustGraph Engine - Docker Deployment
echo ==========================================
echo.

echo [1/4] Building Docker images...
docker-compose build

echo.
echo [2/4] Starting containers...
docker-compose up -d

echo.
echo [3/4] Waiting for services...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Checking health...
docker-compose ps

echo.
echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   View logs: docker-compose logs -f
echo   Stop:      docker-compose down
echo ==========================================
echo.
pause
