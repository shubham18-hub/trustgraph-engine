@echo off
REM TrustGraph Engine - AWS Connection Test (Windows Batch Wrapper)

echo ==========================================
echo TrustGraph - AWS Connection Test
echo ==========================================
echo.
echo This will test connectivity to all AWS services
echo required for TrustGraph Engine deployment.
echo.

set /p region="Enter AWS region (default: ap-south-1): "
if "%region%"=="" set region=ap-south-1

echo.
echo Testing AWS connectivity in region: %region%
echo.
pause

powershell -ExecutionPolicy Bypass -File test-aws-connection.ps1 -Region %region%

echo.
pause
