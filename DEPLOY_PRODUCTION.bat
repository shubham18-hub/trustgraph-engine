@echo off
REM TrustGraph Engine - Production Deployment Script (Windows)
REM This script deploys TrustGraph to production environment

echo ==========================================
echo TrustGraph Engine - Production Deployment
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: AWS CLI is not installed
    echo For AWS deployment, install from https://aws.amazon.com/cli/
    echo.
    echo Continuing with Docker Compose deployment...
    goto :docker_deploy
)

REM Ask deployment method
echo Select deployment method:
echo 1. Docker Compose (Local/Simple)
echo 2. AWS CloudFormation (Serverless)
echo 3. Kubernetes on EKS (Enterprise)
echo.
set /p deploy_method="Enter choice (1-3): "

if "%deploy_method%"=="1" goto :docker_deploy
if "%deploy_method%"=="2" goto :aws_deploy
if "%deploy_method%"=="3" goto :k8s_deploy

echo Invalid choice
pause
exit /b 1

:docker_deploy
echo.
echo ==========================================
echo Docker Compose Deployment
echo ==========================================
echo.

REM Check if .env.production exists
if not exist .env.production (
    echo Creating .env.production from template...
    copy .env.example .env.production
    echo.
    echo IMPORTANT: Edit .env.production with your credentials before continuing
    notepad .env.production
    echo.
    set /p continue="Continue with deployment? (y/n): "
    if /i not "%continue%"=="y" exit /b 0
)

REM Build and start services
echo Building Docker images...
docker-compose build

echo.
echo Starting services...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Health check
echo.
echo Running health check...
curl -f http://localhost:8000/api/health
if errorlevel 1 (
    echo.
    echo WARNING: Health check failed
    echo Check logs with: docker-compose logs
) else (
    echo.
    echo ==========================================
    echo Deployment Successful!
    echo ==========================================
    echo.
    echo Backend API: http://localhost:8000
    echo Frontend UI: http://localhost:3000
    echo.
    echo View logs: docker-compose logs -f
    echo Stop services: docker-compose down
)

pause
exit /b 0

:aws_deploy
echo.
echo ==========================================
echo AWS CloudFormation Deployment
echo ==========================================
echo.

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS credentials not configured
    echo Run: aws configure
    pause
    exit /b 1
)

set /p aws_region="Enter AWS region (default: ap-south-1): "
if "%aws_region%"=="" set aws_region=ap-south-1

echo.
echo Deploying to AWS region: %aws_region%
echo This will create:
echo - S3 buckets for frontend and backups
echo - DynamoDB tables for data storage
echo - Lambda functions for API
echo - CloudFront distribution for CDN
echo - API Gateway for REST API
echo.
set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" exit /b 0

REM Run PowerShell deployment script
powershell -ExecutionPolicy Bypass -File deploy.ps1 -Environment production -Region %aws_region%

pause
exit /b 0

:k8s_deploy
echo.
echo ==========================================
echo Kubernetes on EKS Deployment
echo ==========================================
echo.

REM Check kubectl
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo ERROR: kubectl is not installed
    echo Install from: https://kubernetes.io/docs/tasks/tools/
    pause
    exit /b 1
)

set /p cluster_name="Enter EKS cluster name (default: trustgraph-production): "
if "%cluster_name%"=="" set cluster_name=trustgraph-production

set /p aws_region="Enter AWS region (default: ap-south-1): "
if "%aws_region%"=="" set aws_region=ap-south-1

echo.
echo Updating kubeconfig...
aws eks update-kubeconfig --name %cluster_name% --region %aws_region%

echo.
echo Deploying to Kubernetes...
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/ingress.yaml

echo.
echo Waiting for rollout...
kubectl rollout status deployment/trustgraph-backend -n trustgraph --timeout=5m

echo.
echo ==========================================
echo Deployment Successful!
echo ==========================================
echo.
echo View pods: kubectl get pods -n trustgraph
echo View services: kubectl get svc -n trustgraph
echo View logs: kubectl logs -f deployment/trustgraph-backend -n trustgraph

pause
exit /b 0
