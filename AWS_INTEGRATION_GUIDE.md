# TrustGraph Engine - AWS Integration Guide

## Overview
This guide walks you through connecting TrustGraph Engine to AWS services for production deployment.

## Prerequisites

### 1. AWS Account
- Active AWS account with billing enabled
- Root or IAM user with administrative permissions
- Credit card on file for AWS charges

### 2. AWS CLI Installation

**Windows:**
```powershell
# Download and install from:
https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version
```

**Linux/Mac:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

### 3. AWS Credentials Configuration

```bash
aws configure
```

You'll need:
- **AWS Access Key ID**: From IAM user credentials
- **AWS Secret Access Key**: From IAM user credentials
- **Default region**: `ap-south-1` (Mumbai, India - for DPDP compliance)
- **Default output format**: `json`

## Step-by-Step Integration

### Step 1: Test AWS Connectivity

Before setting up resources, verify your AWS connection:

**Windows:**
```batch
test-aws-connection.bat
```

**PowerShell:**
```powershell
.\test-aws-connection.ps1 -Region ap-south-1
```

This tests connectivity to:
- ✓ AWS CLI installation
- ✓ AWS credentials validity
- ✓ S3 access
- ✓ DynamoDB access
- ✓ Lambda access
- ✓ IAM permissions
- ✓ KMS access
- ✓ Secrets Manager
- ✓ CloudWatch Logs
- ✓ API Gateway
- ✓ Bedrock (AI models)
- ✓ CloudFormation

**Expected Output:**
```
==========================================
Test Summary
==========================================
Total Tests: 12
Passed: 12
Failed: 0
```

### Step 2: Enable AWS Bedrock

Bedrock requires manual model access approval:

1. Go to AWS Console: https://console.aws.amazon.com/bedrock/
2. Navigate to **Model access** in the left sidebar
3. Click **Request model access**
4. Select **Anthropic Claude** models:
   - Claude 3 Sonnet
   - Claude 3 Haiku
   - Claude 2.1
5. Accept terms and submit request
6. Wait for approval (usually instant for most accounts)

**Verify Bedrock Access:**
```powershell
aws bedrock list-foundation-models --region ap-south-1
```

### Step 3: Create AWS Resources

Run the automated setup script to create all required AWS resources:

**Windows:**
```batch
aws-setup.bat
```

**PowerShell:**
```powershell
.\aws-setup.ps1 -Region ap-south-1 -Environment production
```

**What Gets Created:**

1. **S3 Buckets** (2):
   - `trustgraph-{account-id}-frontend-production` - Frontend hosting
   - `trustgraph-{account-id}-backups-production` - Database backups

2. **DynamoDB Tables** (3):
   - `trustgraph-users-production` - User accounts
   - `trustgraph-credentials-production` - Verifiable credentials
   - `trustgraph-transactions-production` - Payment transactions

3. **KMS Keys** (1):
   - Encryption key for sensitive data

4. **IAM Roles** (1):
   - `trustgraph-lambda-role-production` - Lambda execution role

5. **CloudWatch Log Groups** (5):
   - `/aws/lambda/trustgraph-auth-production`
   - `/aws/lambda/trustgraph-voice-production`
   - `/aws/lambda/trustgraph-wallet-production`
   - `/aws/apigateway/trustgraph-production`
   - `/aws/trustgraph/production`

6. **Secrets Manager** (3):
   - `trustgraph/production/jwt-secret`
   - `trustgraph/production/encryption-key`
   - `trustgraph/production/redis-password`

**Output:**
The script generates `aws-config.env` with all resource identifiers.

### Step 4: Update Secrets

The setup script creates placeholder secrets. Update them with real values:

```powershell
# Generate strong secrets
$jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$encryptionKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$redisPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Update secrets
aws secretsmanager update-secret `
    --secret-id trustgraph/production/jwt-secret `
    --secret-string $jwtSecret `
    --region ap-south-1

aws secretsmanager update-secret `
    --secret-id trustgraph/production/encryption-key `
    --secret-string $encryptionKey `
    --region ap-south-1

aws secretsmanager update-secret `
    --secret-id trustgraph/production/redis-password `
    --secret-string $redisPassword `
    --region ap-south-1
```

### Step 5: Configure Environment Variables

Update `.env.production` with AWS configuration from `aws-config.env`:

```bash
# Copy AWS configuration
cat aws-config.env >> .env.production

# Edit .env.production and add API keys
notepad .env.production  # Windows
nano .env.production     # Linux/Mac
```

**Required API Keys:**
- `BHASHINI_API_KEY` - From https://bhashini.gov.in/
- `AADHAAR_API_KEY` - From UIDAI
- `UPI_MERCHANT_ID` - From your payment gateway
- `UPI_MERCHANT_KEY` - From your payment gateway

### Step 6: Verify Configuration

Check that all AWS resources are accessible:

```powershell
# List S3 buckets
aws s3 ls --region ap-south-1 | Select-String "trustgraph"

# List DynamoDB tables
aws dynamodb list-tables --region ap-south-1 | Select-String "trustgraph"

# List secrets
aws secretsmanager list-secrets --region ap-south-1 | Select-String "trustgraph"

# Test Bedrock
aws bedrock list-foundation-models --region ap-south-1 | Select-String "claude"
```

### Step 7: Deploy Application

Choose your deployment method:

#### Option A: Docker Compose (Local/Testing)
```batch
START_PRODUCTION.bat
```

#### Option B: AWS CloudFormation (Production)
```batch
DEPLOY_PRODUCTION.bat
# Select option 2: AWS CloudFormation
```

#### Option C: Kubernetes on EKS (Enterprise)
```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/ingress.yaml
```

## AWS Services Integration Details

### S3 Integration
```python
# In your application code
import boto3

s3_client = boto3.client('s3', region_name='ap-south-1')

# Upload credential
s3_client.put_object(
    Bucket='trustgraph-{account-id}-frontend-production',
    Key=f'credentials/{credential_id}.json',
    Body=json.dumps(credential_data),
    ServerSideEncryption='AES256'
)
```

### DynamoDB Integration
```python
import boto3

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
users_table = dynamodb.Table('trustgraph-users-production')

# Store user
users_table.put_item(
    Item={
        'user_id': user_id,
        'phone': phone_number,
        'created_at': timestamp
    }
)
```

### Bedrock Integration
```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')

# Invoke Claude model
response = bedrock.invoke_model(
    modelId='anthropic.claude-v2',
    body=json.dumps({
        'prompt': f'\n\nHuman: {user_query}\n\nAssistant:',
        'max_tokens_to_sample': 300,
        'temperature': 0.7
    })
)
```

### KMS Integration
```python
import boto3

kms_client = boto3.client('kms', region_name='ap-south-1')

# Encrypt data
response = kms_client.encrypt(
    KeyId='alias/trustgraph-production',
    Plaintext=sensitive_data
)
encrypted_data = response['CiphertextBlob']
```

### Secrets Manager Integration
```python
import boto3
import json

secrets_client = boto3.client('secretsmanager', region_name='ap-south-1')

# Retrieve secret
response = secrets_client.get_secret_value(
    SecretId='trustgraph/production/jwt-secret'
)
jwt_secret = response['SecretString']
```

## Cost Estimation

### Monthly Costs (Estimated)

**Development/Testing (1,000 users):**
- S3: $1-5
- DynamoDB: $5-10 (on-demand)
- Lambda: $0-5 (free tier)
- Bedrock: $10-20
- CloudWatch: $5
- **Total: ~$25-45/month**

**Production (100,000 users):**
- S3: $10-20
- DynamoDB: $50-100
- Lambda: $20-50
- Bedrock: $100-200
- CloudWatch: $20
- Data Transfer: $50
- **Total: ~$250-440/month**

**Scale (1,000,000 users):**
- S3: $50-100
- DynamoDB: $500-1,000
- Lambda: $200-500
- Bedrock: $1,000-2,000
- CloudWatch: $100
- Data Transfer: $500
- **Total: ~$2,350-4,200/month**

### Cost Optimization Tips

1. **Use Reserved Capacity** for predictable workloads
2. **Enable S3 Lifecycle Policies** to archive old data
3. **Use DynamoDB On-Demand** for variable traffic
4. **Implement Caching** with Redis to reduce Bedrock calls
5. **Set CloudWatch Log Retention** to 30 days
6. **Use Spot Instances** for non-critical workloads

## Security Best Practices

### 1. IAM Least Privilege
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:Query"
    ],
    "Resource": "arn:aws:dynamodb:ap-south-1:*:table/trustgraph-*"
  }]
}
```

### 2. Enable MFA for AWS Console
```bash
aws iam enable-mfa-device \
  --user-name your-username \
  --serial-number arn:aws:iam::ACCOUNT_ID:mfa/your-username \
  --authentication-code1 123456 \
  --authentication-code2 789012
```

### 3. Enable CloudTrail Logging
```bash
aws cloudtrail create-trail \
  --name trustgraph-audit \
  --s3-bucket-name trustgraph-audit-logs \
  --is-multi-region-trail
```

### 4. Enable GuardDuty
```bash
aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES
```

## Monitoring & Alerts

### CloudWatch Dashboard
```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name TrustGraph-Production \
  --dashboard-body file://monitoring/dashboard.json
```

### Set Up Alarms
```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name trustgraph-high-errors \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Issue: "Access Denied" Errors
**Solution:**
```bash
# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME

# Attach required policies
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### Issue: Bedrock Models Not Available
**Solution:**
1. Go to AWS Console > Bedrock > Model access
2. Request access to Claude models
3. Wait for approval (usually instant)
4. Verify: `aws bedrock list-foundation-models --region ap-south-1`

### Issue: DynamoDB Throttling
**Solution:**
```bash
# Enable auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id "table/trustgraph-users-production" \
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" \
  --min-capacity 5 \
  --max-capacity 100
```

### Issue: High Costs
**Solution:**
```bash
# Check cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Set budget alerts
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget file://budget.json
```

## Next Steps

1. ✓ Test AWS connectivity
2. ✓ Create AWS resources
3. ✓ Update secrets
4. ✓ Configure environment
5. ✓ Deploy application
6. ⬜ Set up monitoring
7. ⬜ Configure backups
8. ⬜ Enable auto-scaling
9. ⬜ Set up CI/CD
10. ⬜ Perform load testing

## Support

- **AWS Support**: https://console.aws.amazon.com/support/
- **TrustGraph Issues**: https://github.com/your-org/trustgraph/issues
- **Documentation**: See `DEPLOYMENT_GUIDE.md` and `PRODUCTION_DEPLOYMENT.md`

---

**Status**: Ready for AWS Integration ✓
