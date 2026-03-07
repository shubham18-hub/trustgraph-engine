# TrustGraph Engine - AWS Connection Test
# This script tests connectivity to all required AWS services

param(
    [string]$Region = "ap-south-1"
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TrustGraph - AWS Connection Test" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$testResults = @()
$passCount = 0
$failCount = 0

function Test-Service {
    param(
        [string]$Name,
        [scriptblock]$TestCommand
    )
    
    Write-Host "Testing $Name..." -NoNewline
    try {
        $result = & $TestCommand
        Write-Host " ✓ PASS" -ForegroundColor Green
        $script:passCount++
        return @{
            Service = $Name
            Status = "PASS"
            Details = $result
        }
    } catch {
        Write-Host " ✗ FAIL" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
        $script:failCount++
        return @{
            Service = $Name
            Status = "FAIL"
            Details = $_.Exception.Message
        }
    }
}

# Test 1: AWS CLI
Write-Host "[1/12] AWS CLI Installation" -ForegroundColor Yellow
$testResults += Test-Service "AWS CLI" {
    $version = aws --version 2>&1
    return $version
}

# Test 2: AWS Credentials
Write-Host "[2/12] AWS Credentials" -ForegroundColor Yellow
$testResults += Test-Service "AWS Credentials" {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    return "Account: $($identity.Account), User: $($identity.Arn)"
}

# Test 3: S3 Access
Write-Host "[3/12] S3 Service" -ForegroundColor Yellow
$testResults += Test-Service "S3 Access" {
    $buckets = aws s3 ls --region $Region 2>&1
    return "S3 accessible, found $($buckets.Count) buckets"
}

# Test 4: DynamoDB Access
Write-Host "[4/12] DynamoDB Service" -ForegroundColor Yellow
$testResults += Test-Service "DynamoDB Access" {
    $tables = aws dynamodb list-tables --region $Region --output json | ConvertFrom-Json
    return "DynamoDB accessible, found $($tables.TableNames.Count) tables"
}

# Test 5: Lambda Access
Write-Host "[5/12] Lambda Service" -ForegroundColor Yellow
$testResults += Test-Service "Lambda Access" {
    $functions = aws lambda list-functions --region $Region --output json | ConvertFrom-Json
    return "Lambda accessible, found $($functions.Functions.Count) functions"
}

# Test 6: IAM Access
Write-Host "[6/12] IAM Service" -ForegroundColor Yellow
$testResults += Test-Service "IAM Access" {
    $roles = aws iam list-roles --max-items 1 --output json | ConvertFrom-Json
    return "IAM accessible"
}

# Test 7: KMS Access
Write-Host "[7/12] KMS Service" -ForegroundColor Yellow
$testResults += Test-Service "KMS Access" {
    $keys = aws kms list-keys --region $Region --output json | ConvertFrom-Json
    return "KMS accessible, found $($keys.Keys.Count) keys"
}

# Test 8: Secrets Manager
Write-Host "[8/12] Secrets Manager" -ForegroundColor Yellow
$testResults += Test-Service "Secrets Manager" {
    $secrets = aws secretsmanager list-secrets --region $Region --output json | ConvertFrom-Json
    return "Secrets Manager accessible, found $($secrets.SecretList.Count) secrets"
}

# Test 9: CloudWatch Logs
Write-Host "[9/12] CloudWatch Logs" -ForegroundColor Yellow
$testResults += Test-Service "CloudWatch Logs" {
    $logGroups = aws logs describe-log-groups --region $Region --max-items 1 --output json | ConvertFrom-Json
    return "CloudWatch Logs accessible"
}

# Test 10: API Gateway
Write-Host "[10/12] API Gateway" -ForegroundColor Yellow
$testResults += Test-Service "API Gateway" {
    $apis = aws apigatewayv2 get-apis --region $Region --output json | ConvertFrom-Json
    return "API Gateway accessible, found $($apis.Items.Count) APIs"
}

# Test 11: Bedrock
Write-Host "[11/12] Bedrock Service" -ForegroundColor Yellow
$testResults += Test-Service "Bedrock Access" {
    $models = aws bedrock list-foundation-models --region $Region --output json 2>&1 | ConvertFrom-Json
    $claudeModels = $models.modelSummaries | Where-Object { $_.modelId -like "*claude*" }
    if ($claudeModels) {
        return "Bedrock accessible, Claude models available"
    } else {
        throw "Bedrock accessible but no Claude models found. Request model access in AWS Console."
    }
}

# Test 12: CloudFormation
Write-Host "[12/12] CloudFormation Service" -ForegroundColor Yellow
$testResults += Test-Service "CloudFormation" {
    $stacks = aws cloudformation list-stacks --region $Region --output json | ConvertFrom-Json
    return "CloudFormation accessible, found $($stacks.StackSummaries.Count) stacks"
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Total Tests: $($testResults.Count)" -ForegroundColor White
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Detailed Results
Write-Host "Detailed Results:" -ForegroundColor Yellow
Write-Host ""
foreach ($result in $testResults) {
    $statusColor = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "  $($result.Service): " -NoNewline
    Write-Host "$($result.Status)" -ForegroundColor $statusColor
    if ($result.Details) {
        Write-Host "    $($result.Details)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan

# Check for TrustGraph resources
Write-Host ""
Write-Host "Checking for TrustGraph Resources..." -ForegroundColor Yellow
Write-Host ""

# Check S3 buckets
Write-Host "S3 Buckets:" -ForegroundColor Cyan
try {
    $buckets = aws s3 ls --region $Region 2>&1 | Select-String "trustgraph"
    if ($buckets) {
        foreach ($bucket in $buckets) {
            Write-Host "  ✓ $bucket" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠ No TrustGraph buckets found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error checking buckets" -ForegroundColor Red
}

# Check DynamoDB tables
Write-Host ""
Write-Host "DynamoDB Tables:" -ForegroundColor Cyan
try {
    $tables = aws dynamodb list-tables --region $Region --output json | ConvertFrom-Json
    $trustgraphTables = $tables.TableNames | Where-Object { $_ -like "trustgraph-*" }
    if ($trustgraphTables) {
        foreach ($table in $trustgraphTables) {
            Write-Host "  ✓ $table" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠ No TrustGraph tables found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error checking tables" -ForegroundColor Red
}

# Check Lambda functions
Write-Host ""
Write-Host "Lambda Functions:" -ForegroundColor Cyan
try {
    $functions = aws lambda list-functions --region $Region --output json | ConvertFrom-Json
    $trustgraphFunctions = $functions.Functions | Where-Object { $_.FunctionName -like "trustgraph-*" }
    if ($trustgraphFunctions) {
        foreach ($function in $trustgraphFunctions) {
            Write-Host "  ✓ $($function.FunctionName)" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠ No TrustGraph functions found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error checking functions" -ForegroundColor Red
}

# Check CloudWatch log groups
Write-Host ""
Write-Host "CloudWatch Log Groups:" -ForegroundColor Cyan
try {
    $logGroups = aws logs describe-log-groups --region $Region --output json | ConvertFrom-Json
    $trustgraphLogs = $logGroups.logGroups | Where-Object { $_.logGroupName -like "*trustgraph*" }
    if ($trustgraphLogs) {
        foreach ($log in $trustgraphLogs) {
            Write-Host "  ✓ $($log.logGroupName)" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠ No TrustGraph log groups found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Error checking log groups" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan

# Recommendations
if ($failCount -gt 0) {
    Write-Host ""
    Write-Host "Recommendations:" -ForegroundColor Yellow
    Write-Host ""
    
    $failedServices = $testResults | Where-Object { $_.Status -eq "FAIL" }
    foreach ($service in $failedServices) {
        Write-Host "  • $($service.Service):" -ForegroundColor Red
        
        switch ($service.Service) {
            "AWS CLI" {
                Write-Host "    Install AWS CLI: https://aws.amazon.com/cli/" -ForegroundColor White
            }
            "AWS Credentials" {
                Write-Host "    Run: aws configure" -ForegroundColor White
                Write-Host "    Enter your AWS Access Key ID and Secret Access Key" -ForegroundColor White
            }
            "Bedrock Access" {
                Write-Host "    Enable Bedrock model access in AWS Console:" -ForegroundColor White
                Write-Host "    AWS Console > Bedrock > Model access > Request access" -ForegroundColor White
            }
            default {
                Write-Host "    Check IAM permissions for $($service.Service)" -ForegroundColor White
            }
        }
        Write-Host ""
    }
}

# Next steps
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
if ($passCount -eq $testResults.Count) {
    Write-Host "  ✓ All AWS services accessible!" -ForegroundColor Green
    Write-Host "  1. Run: .\aws-setup.bat to create TrustGraph resources" -ForegroundColor White
    Write-Host "  2. Configure API keys in .env.production" -ForegroundColor White
    Write-Host "  3. Deploy: .\DEPLOY_PRODUCTION.bat" -ForegroundColor White
} else {
    Write-Host "  1. Fix failed service connections (see recommendations above)" -ForegroundColor White
    Write-Host "  2. Re-run this test: .\test-aws-connection.ps1" -ForegroundColor White
    Write-Host "  3. Once all tests pass, run: .\aws-setup.bat" -ForegroundColor White
}

Write-Host ""
