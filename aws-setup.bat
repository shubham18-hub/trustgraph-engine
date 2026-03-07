@echo off
REM TrustGraph Engine - AWS Setup (Windows Batch Wrapper)
REM This script calls the PowerShell setup script

echo ==========================================
echo TrustGraph Engine - AWS Setup
echo ==========================================
echo.

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell available'" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell not found
    echo Please install PowerShell or run aws-setup.ps1 directly
    pause
    exit /b 1
)

echo This script will configure AWS services for TrustGraph:
echo   - S3 buckets for storage
echo   - DynamoDB tables for data
echo   - KMS keys for encryption
echo   - IAM roles for permissions
echo   - CloudWatch for logging
echo   - Secrets Manager for credentials
echo.

set /p region="Enter AWS region (default: ap-south-1): "
if "%region%"=="" set region=ap-south-1

set /p environment="Enter environment (default: production): "
if "%environment%"=="" set environment=production

echo.
set /p dryrun="Dry run mode? (y/n, default: n): "
if /i "%dryrun%"=="y" (
    set dryrun_flag=-DryRun
) else (
    set dryrun_flag=
)

echo.
echo Configuration:
echo   Region: %region%
echo   Environment: %environment%
echo   Dry Run: %dryrun%
echo.
set /p confirm="Continue with AWS setup? (y/n): "
if /i not "%confirm%"=="y" (
    echo Setup cancelled
    pause
    exit /b 0
)

echo.
echo Running AWS setup...
echo.

powershell -ExecutionPolicy Bypass -File aws-setup.ps1 -Region %region% -Environment %environment% %dryrun_flag%

if errorlevel 1 (
    echo.
    echo ERROR: AWS setup failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ==========================================
echo AWS Setup Complete!
echo ==========================================
echo.
echo Configuration saved to: aws-config.env
echo.
echo Next steps:
echo   1. Review aws-config.env
echo   2. Update .env.production with AWS values
echo   3. Configure API keys (Bhashini, Aadhaar, UPI)
echo   4. Deploy: DEPLOY_PRODUCTION.bat
echo.
pause
