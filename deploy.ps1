# TrustGraph Engine - AWS Deployment Script (PowerShell)
param(
    [string]$Environment = "production",
    [string]$Region = "ap-south-1"
)

$ErrorActionPreference = "Stop"
$StackName = "trustgraph-$Environment"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TrustGraph Engine - AWS Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment"
Write-Host "Region: $Region"
Write-Host "Stack: $StackName"
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Build Frontend
Write-Host "[1/7] Building frontend..." -ForegroundColor Yellow
Set-Location frontend

if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Minify CSS
Write-Host "Minifying CSS..."
Get-Content styles.css, themes.css, accessibility.css | Set-Content dist/bundle.css

# Minify JS
Write-Host "Minifying JavaScript..."
Get-Content app.js, voice.js | Set-Content dist/bundle.js

# Copy files
Copy-Item index.html dist/
Copy-Item theme-config.json dist/

Set-Location ..

# Step 2: Deploy CloudFormation Stack
Write-Host "[2/7] Deploying CloudFormation stack..." -ForegroundColor Yellow
aws cloudformation deploy `
    --template-file infrastructure/cloudformation-stack.yaml `
    --stack-name $StackName `
    --parameter-overrides Environment=$Environment `
    --capabilities CAPABILITY_NAMED_IAM `
    --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "CloudFormation deployment failed" -ForegroundColor Red
    exit 1
}

# Get stack outputs
Write-Host "Getting stack outputs..."
$BucketName = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' `
    --output text `
    --region $Region

$DistributionId = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' `
    --output text `
    --region $Region

$ApiEndpoint = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' `
    --output text `
    --region $Region

Write-Host "Bucket: $BucketName" -ForegroundColor Green
Write-Host "Distribution: $DistributionId" -ForegroundColor Green
Write-Host "API: $ApiEndpoint" -ForegroundColor Green

# Step 3: Upload Frontend to S3
Write-Host "[3/7] Uploading frontend to S3..." -ForegroundColor Yellow
aws s3 sync frontend/dist s3://$BucketName/ `
    --delete `
    --cache-control "public, max-age=31536000" `
    --region $Region

# Upload HTML with no-cache
aws s3 cp frontend/dist/index.html s3://${BucketName}/index.html `
    --cache-control "no-cache" `
    --content-type "text/html" `
    --region $Region

# Step 4: Invalidate CloudFront Cache
Write-Host "[4/7] Invalidating CloudFront cache..." -ForegroundColor Yellow
aws cloudfront create-invalidation `
    --distribution-id $DistributionId `
    --paths "/*" `
    --region $Region

# Step 5: Deploy Lambda Functions
Write-Host "[5/7] Deploying Lambda functions..." -ForegroundColor Yellow

# Package Lambda functions
Set-Location src
Compress-Archive -Path services/auth_service.py, core/* -DestinationPath ../lambda-auth.zip -Force
Compress-Archive -Path services/voice_service.py, services/bedrock_service.py, core/* -DestinationPath ../lambda-voice.zip -Force
Set-Location ..

# Update Lambda functions
aws lambda update-function-code `
    --function-name trustgraph-auth-$Environment `
    --zip-file fileb://lambda-auth.zip `
    --region $Region

aws lambda update-function-code `
    --function-name trustgraph-voice-$Environment `
    --zip-file fileb://lambda-voice.zip `
    --region $Region

# Cleanup
Remove-Item lambda-auth.zip, lambda-voice.zip

# Step 6: Configure API Gateway Routes
Write-Host "[6/7] Configuring API Gateway..." -ForegroundColor Yellow
# Routes are configured via CloudFormation

# Step 7: Health Check
Write-Host "[7/7] Running health check..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$HealthUrl = "$ApiEndpoint/health"
Write-Host "Checking: $HealthUrl"

try {
    $Response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing
    if ($Response.StatusCode -eq 200) {
        Write-Host "✓ Health check passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Health check failed (HTTP $($Response.StatusCode))" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Frontend URL: https://$DistributionId.cloudfront.net"
Write-Host "API Endpoint: $ApiEndpoint"
Write-Host "==========================================" -ForegroundColor Cyan
