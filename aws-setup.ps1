# TrustGraph Engine - AWS Services Setup Script
# This script configures and connects all required AWS services

param(
    [string]$Region = "ap-south-1",
    [string]$Environment = "production",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TrustGraph Engine - AWS Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Region: $Region"
Write-Host "Environment: $Environment"
Write-Host "Dry Run: $DryRun"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI installation
Write-Host "[1/10] Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version
    Write-Host "✓ AWS CLI installed: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found. Please install from https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host ""
Write-Host "[2/10] Verifying AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✓ AWS Account: $($identity.Account)" -ForegroundColor Green
    Write-Host "✓ User/Role: $($identity.Arn)" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}

# Set variables
$AccountId = $identity.Account
$StackName = "trustgraph-$Environment"
$BucketPrefix = "trustgraph-$AccountId"

Write-Host ""
Write-Host "[3/10] Creating S3 Buckets..." -ForegroundColor Yellow

# Frontend bucket
$FrontendBucket = "$BucketPrefix-frontend-$Environment"
Write-Host "Creating frontend bucket: $FrontendBucket"
if (-not $DryRun) {
    try {
        aws s3 mb "s3://$FrontendBucket" --region $Region 2>$null
        Write-Host "✓ Frontend bucket created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Bucket may already exist" -ForegroundColor Yellow
    }
    
    # Enable versioning
    aws s3api put-bucket-versioning `
        --bucket $FrontendBucket `
        --versioning-configuration Status=Enabled `
        --region $Region
    
    # Enable encryption
    aws s3api put-bucket-encryption `
        --bucket $FrontendBucket `
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }' `
        --region $Region
    
    Write-Host "✓ Bucket configured with versioning and encryption" -ForegroundColor Green
}

# Backup bucket
$BackupBucket = "$BucketPrefix-backups-$Environment"
Write-Host "Creating backup bucket: $BackupBucket"
if (-not $DryRun) {
    try {
        aws s3 mb "s3://$BackupBucket" --region $Region 2>$null
        Write-Host "✓ Backup bucket created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Bucket may already exist" -ForegroundColor Yellow
    }
    
    # Enable versioning and lifecycle
    aws s3api put-bucket-versioning `
        --bucket $BackupBucket `
        --versioning-configuration Status=Enabled `
        --region $Region
    
    # Lifecycle policy for backups
    $lifecyclePolicy = @"
{
    "Rules": [{
        "Id": "DeleteOldBackups",
        "Status": "Enabled",
        "Prefix": "",
        "Transitions": [{
            "Days": 30,
            "StorageClass": "GLACIER"
        }],
        "Expiration": {
            "Days": 90
        }
    }]
}
"@
    $lifecyclePolicy | Out-File -FilePath "temp-lifecycle.json" -Encoding UTF8
    aws s3api put-bucket-lifecycle-configuration `
        --bucket $BackupBucket `
        --lifecycle-configuration file://temp-lifecycle.json `
        --region $Region
    Remove-Item "temp-lifecycle.json"
    
    Write-Host "✓ Backup bucket configured with lifecycle policy" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/10] Creating DynamoDB Tables..." -ForegroundColor Yellow

# Users table
$UsersTable = "trustgraph-users-$Environment"
Write-Host "Creating users table: $UsersTable"
if (-not $DryRun) {
    try {
        aws dynamodb create-table `
            --table-name $UsersTable `
            --attribute-definitions `
                AttributeName=user_id,AttributeType=S `
                AttributeName=phone,AttributeType=S `
            --key-schema AttributeName=user_id,KeyType=HASH `
            --global-secondary-indexes `
                "[{
                    \"IndexName\": \"phone-index\",
                    \"KeySchema\": [{\"AttributeName\":\"phone\",\"KeyType\":\"HASH\"}],
                    \"Projection\": {\"ProjectionType\":\"ALL\"},
                    \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
                }]" `
            --billing-mode PAY_PER_REQUEST `
            --region $Region `
            --tags Key=Environment,Value=$Environment Key=Project,Value=TrustGraph
        Write-Host "✓ Users table created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Table may already exist" -ForegroundColor Yellow
    }
}

# Credentials table
$CredentialsTable = "trustgraph-credentials-$Environment"
Write-Host "Creating credentials table: $CredentialsTable"
if (-not $DryRun) {
    try {
        aws dynamodb create-table `
            --table-name $CredentialsTable `
            --attribute-definitions `
                AttributeName=credential_id,AttributeType=S `
                AttributeName=worker_id,AttributeType=S `
            --key-schema AttributeName=credential_id,KeyType=HASH `
            --global-secondary-indexes `
                "[{
                    \"IndexName\": \"worker-index\",
                    \"KeySchema\": [{\"AttributeName\":\"worker_id\",\"KeyType\":\"HASH\"}],
                    \"Projection\": {\"ProjectionType\":\"ALL\"},
                    \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
                }]" `
            --billing-mode PAY_PER_REQUEST `
            --region $Region `
            --tags Key=Environment,Value=$Environment Key=Project,Value=TrustGraph
        Write-Host "✓ Credentials table created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Table may already exist" -ForegroundColor Yellow
    }
}

# Transactions table
$TransactionsTable = "trustgraph-transactions-$Environment"
Write-Host "Creating transactions table: $TransactionsTable"
if (-not $DryRun) {
    try {
        aws dynamodb create-table `
            --table-name $TransactionsTable `
            --attribute-definitions `
                AttributeName=transaction_id,AttributeType=S `
                AttributeName=worker_id,AttributeType=S `
                AttributeName=timestamp,AttributeType=N `
            --key-schema AttributeName=transaction_id,KeyType=HASH `
            --global-secondary-indexes `
                "[{
                    \"IndexName\": \"worker-timestamp-index\",
                    \"KeySchema\": [
                        {\"AttributeName\":\"worker_id\",\"KeyType\":\"HASH\"},
                        {\"AttributeName\":\"timestamp\",\"KeyType\":\"RANGE\"}
                    ],
                    \"Projection\": {\"ProjectionType\":\"ALL\"},
                    \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
                }]" `
            --billing-mode PAY_PER_REQUEST `
            --region $Region `
            --tags Key=Environment,Value=$Environment Key=Project,Value=TrustGraph
        Write-Host "✓ Transactions table created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Table may already exist" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[5/10] Creating KMS Keys..." -ForegroundColor Yellow
if (-not $DryRun) {
    try {
        $kmsKey = aws kms create-key `
            --description "TrustGraph encryption key for $Environment" `
            --key-usage ENCRYPT_DECRYPT `
            --origin AWS_KMS `
            --tags TagKey=Environment,TagValue=$Environment TagKey=Project,TagValue=TrustGraph `
            --region $Region `
            --output json | ConvertFrom-Json
        
        $KeyId = $kmsKey.KeyMetadata.KeyId
        
        # Create alias
        aws kms create-alias `
            --alias-name "alias/trustgraph-$Environment" `
            --target-key-id $KeyId `
            --region $Region
        
        Write-Host "✓ KMS key created: $KeyId" -ForegroundColor Green
    } catch {
        Write-Host "⚠ KMS key may already exist" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[6/10] Creating IAM Role for Lambda..." -ForegroundColor Yellow
if (-not $DryRun) {
    $trustPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}
"@
    $trustPolicy | Out-File -FilePath "temp-trust-policy.json" -Encoding UTF8
    
    try {
        aws iam create-role `
            --role-name "trustgraph-lambda-role-$Environment" `
            --assume-role-policy-document file://temp-trust-policy.json `
            --description "TrustGraph Lambda execution role" `
            --tags Key=Environment,Value=$Environment Key=Project,Value=TrustGraph
        
        # Attach managed policies
        aws iam attach-role-policy `
            --role-name "trustgraph-lambda-role-$Environment" `
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        aws iam attach-role-policy `
            --role-name "trustgraph-lambda-role-$Environment" `
            --policy-arn "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
        
        Write-Host "✓ IAM role created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ IAM role may already exist" -ForegroundColor Yellow
    }
    
    Remove-Item "temp-trust-policy.json"
    
    # Create custom policy for DynamoDB and Bedrock
    $customPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:$Region:$AccountId:table/trustgraph-*",
                "arn:aws:dynamodb:$Region:$AccountId:table/trustgraph-*/index/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt",
                "kms:Encrypt",
                "kms:GenerateDataKey"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::$BucketPrefix-*/*"
        }
    ]
}
"@
    $customPolicy | Out-File -FilePath "temp-custom-policy.json" -Encoding UTF8
    
    try {
        aws iam put-role-policy `
            --role-name "trustgraph-lambda-role-$Environment" `
            --policy-name "TrustGraphCustomPolicy" `
            --policy-document file://temp-custom-policy.json
        Write-Host "✓ Custom IAM policy attached" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Policy may already exist" -ForegroundColor Yellow
    }
    
    Remove-Item "temp-custom-policy.json"
}

Write-Host ""
Write-Host "[7/10] Creating CloudWatch Log Groups..." -ForegroundColor Yellow
if (-not $DryRun) {
    $logGroups = @(
        "/aws/lambda/trustgraph-auth-$Environment",
        "/aws/lambda/trustgraph-voice-$Environment",
        "/aws/lambda/trustgraph-wallet-$Environment",
        "/aws/apigateway/trustgraph-$Environment",
        "/aws/trustgraph/$Environment"
    )
    
    foreach ($logGroup in $logGroups) {
        try {
            aws logs create-log-group --log-group-name $logGroup --region $Region
            aws logs put-retention-policy `
                --log-group-name $logGroup `
                --retention-in-days 30 `
                --region $Region
            Write-Host "✓ Created log group: $logGroup" -ForegroundColor Green
        } catch {
            Write-Host "⚠ Log group may already exist: $logGroup" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "[8/10] Checking Bedrock Access..." -ForegroundColor Yellow
try {
    $models = aws bedrock list-foundation-models --region $Region --output json | ConvertFrom-Json
    $claudeModel = $models.modelSummaries | Where-Object { $_.modelId -like "*claude*" } | Select-Object -First 1
    
    if ($claudeModel) {
        Write-Host "✓ Bedrock access confirmed" -ForegroundColor Green
        Write-Host "  Available model: $($claudeModel.modelId)" -ForegroundColor Cyan
    } else {
        Write-Host "⚠ No Claude models found. You may need to request model access in AWS Console" -ForegroundColor Yellow
        Write-Host "  Go to: AWS Console > Bedrock > Model access" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Bedrock not available in region or access not granted" -ForegroundColor Yellow
    Write-Host "  Enable Bedrock in AWS Console: Bedrock > Model access" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[9/10] Creating Secrets in Secrets Manager..." -ForegroundColor Yellow
if (-not $DryRun) {
    $secrets = @{
        "trustgraph/$Environment/jwt-secret" = "CHANGE-THIS-JWT-SECRET-$(Get-Random)"
        "trustgraph/$Environment/encryption-key" = "CHANGE-THIS-ENCRYPTION-KEY-$(Get-Random)"
        "trustgraph/$Environment/redis-password" = "CHANGE-THIS-REDIS-PASSWORD-$(Get-Random)"
    }
    
    foreach ($secretName in $secrets.Keys) {
        try {
            aws secretsmanager create-secret `
                --name $secretName `
                --description "TrustGraph secret for $Environment" `
                --secret-string $secrets[$secretName] `
                --region $Region `
                --tags Key=Environment,Value=$Environment Key=Project,Value=TrustGraph
            Write-Host "✓ Created secret: $secretName" -ForegroundColor Green
        } catch {
            Write-Host "⚠ Secret may already exist: $secretName" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "⚠ IMPORTANT: Update these secrets with real values!" -ForegroundColor Yellow
    Write-Host "  Use: aws secretsmanager update-secret --secret-id <name> --secret-string <value>" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[10/10] Generating Configuration File..." -ForegroundColor Yellow

$config = @"
# TrustGraph Engine - AWS Configuration
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

AWS_REGION=$Region
AWS_ACCOUNT_ID=$AccountId
ENVIRONMENT=$Environment

# S3 Buckets
S3_FRONTEND_BUCKET=$FrontendBucket
S3_BACKUP_BUCKET=$BackupBucket

# DynamoDB Tables
DYNAMODB_USERS_TABLE=$UsersTable
DYNAMODB_CREDENTIALS_TABLE=$CredentialsTable
DYNAMODB_TRANSACTIONS_TABLE=$TransactionsTable

# IAM
IAM_LAMBDA_ROLE=arn:aws:iam::${AccountId}:role/trustgraph-lambda-role-$Environment

# CloudWatch
CLOUDWATCH_LOG_GROUP=/aws/trustgraph/$Environment

# Secrets Manager
SECRET_JWT=trustgraph/$Environment/jwt-secret
SECRET_ENCRYPTION=trustgraph/$Environment/encryption-key
SECRET_REDIS=trustgraph/$Environment/redis-password

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-v2
BEDROCK_REGION=$Region

# Next Steps:
# 1. Update secrets in AWS Secrets Manager with real values
# 2. Request Bedrock model access if not already done
# 3. Configure API keys for Bhashini, Aadhaar, UPI
# 4. Update .env.production with these values
# 5. Deploy application using deploy.ps1 or docker-compose
"@

$config | Out-File -FilePath "aws-config.env" -Encoding UTF8
Write-Host "✓ Configuration saved to: aws-config.env" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AWS Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resources Created:" -ForegroundColor Yellow
Write-Host "  ✓ S3 Buckets: 2 (frontend, backups)"
Write-Host "  ✓ DynamoDB Tables: 3 (users, credentials, transactions)"
Write-Host "  ✓ KMS Keys: 1 (encryption)"
Write-Host "  ✓ IAM Roles: 1 (Lambda execution)"
Write-Host "  ✓ CloudWatch Log Groups: 5"
Write-Host "  ✓ Secrets Manager: 3 secrets"
Write-Host ""
Write-Host "Configuration file: aws-config.env" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review and update secrets in AWS Secrets Manager"
Write-Host "  2. Enable Bedrock model access (if needed)"
Write-Host "  3. Update .env.production with aws-config.env values"
Write-Host "  4. Deploy: .\deploy.ps1 -Environment $Environment -Region $Region"
Write-Host ""
