@echo off
REM TrustGraph Engine - Quick Start Production Script
REM This script starts the production environment locally using Docker Compose

echo ==========================================
echo TrustGraph Engine - Production Start
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

REM Check if .env.production exists
if not exist .env.production (
    echo ERROR: .env.production file not found
    echo.
    echo Creating from template...
    copy .env.example .env.production
    echo.
    echo IMPORTANT: Edit .env.production with your credentials
    notepad .env.production
    echo.
    set /p continue="Continue? (y/n): "
    if /i not "%continue%"=="y" exit /b 0
)

REM Stop any running containers
echo Stopping existing containers...
docker-compose down >nul 2>&1

REM Pull latest images
echo.
echo Pulling latest images...
docker-compose pull

REM Start services
echo.
echo Starting services...
docker-compose up -d

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start services
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
)

REM Wait for services to be ready
echo.
echo Waiting for services to start...
timeout /t 15 /nobreak >nul

REM Health check
echo.
echo Running health check...
echo.

set health_ok=0
for /L %%i in (1,1,5) do (
    curl -f http://localhost:8000/api/health >nul 2>&1
    if not errorlevel 1 (
        set health_ok=1
        goto :health_success
    )
    echo Attempt %%i/5 failed, retrying...
    timeout /t 5 /nobreak >nul
)

:health_success
if %health_ok%==1 (
    echo.
    echo ==========================================
    echo TrustGraph Engine Started Successfully!
    echo ==========================================
    echo.
    echo Backend API: http://localhost:8000
    echo Frontend UI: http://localhost:3000
    echo Redis Cache: localhost:6379
    echo.
    echo API Documentation: http://localhost:8000/docs
    echo Health Check: http://localhost:8000/api/health
    echo.
    echo Useful Commands:
    echo   View logs: docker-compose logs -f
    echo   Stop services: docker-compose down
    echo   Restart: docker-compose restart
    echo   View status: docker-compose ps
    echo.
    echo Opening browser...
    timeout /t 2 /nobreak >nul
    start http://localhost:3000
) else (
    echo.
    echo WARNING: Health check failed
    echo Services may still be starting up
    echo.
    echo Check status with: docker-compose ps
    echo Check logs with: docker-compose logs
)

echo.
echo Press any key to view logs (Ctrl+C to exit)...
pause >nul

docker-compose logs -f
