# TrustGraph Engine - Production Deployment Guide

## System Health Status
Current system health: **62.5%** (5/8 components operational)

### Working Components ✅
- Database (SQLite with all tables)
- Authentication Service (signup/login with OTP)
- AWS Bedrock Service (client initialized)
- Frontend (all files present)
- API Endpoints (33 endpoints)

### Issues to Fix ⚠️
1. **AWS Bedrock Permissions** - User needs `bedrock:InvokeModel` permission
2. **Voice Service** - Needs Bhashini API key configuration
3. **Blockchain Service** - Needs Hyperledger Fabric network setup
4. **UPI Service** - Needs payment gateway credentials

---

## Prerequisites

### 1. AWS Account Setup
- AWS Account with admin access
- AWS CLI installed and configured
- Region: `ap-south-1` (Mumbai) for DPDP Act compliance

### 2. Required AWS Services
- Amazon Bedrock (Claude 3 Haiku model access)
- AWS Lambda
- Amazon API Gateway
- Amazon S3
- Amazon DynamoDB
- AWS KMS
- Amazon CloudFront
- AWS Secrets Manager

### 3. External Services
- Bhashini API key (for multilingual voice support)
- UPI Gateway credentials (Paytm/PhonePe)
- Domain name and SSL certificate

---

## Step 1: Fix AWS Bedrock Permissions

### Current Error
```
User: arn:aws:iam::868422695661:user/Shubham is not authorized to perform: 
bedrock:InvokeModel on resource: arn:aws:bedrock:ap-south-1::foundation-model/
anthropic.claude-3-haiku-20240307-v1:0
```

### Solution: Add IAM Policy

Create and attach this IAM policy to user `Shubham`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    },
    {
      "Sid": "BedrockListModels",
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### AWS CLI Command
```bash
# Create policy file
cat > bedrock-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-south-1::foundation-model/*"
      ]
    }
  ]
}
EOF

# Create IAM policy
aws iam create-policy \
  --policy-name TrustGraphBedrockAccess \
  --policy-document file://bedrock-policy.json \
  --region ap-south-1

# Attach to user
aws iam attach-user-policy \
  --user-name Shubham \
  --policy-arn arn:aws:iam::868422695661:policy/TrustGraphBedrockAccess
```

---

## Step 2: Configure Environment Variables

Create `.env` file in project root:

```bash
# AWS Configuration
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=868422695661

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_REGION=ap-south-1

# Bhashini API (for voice services)
BHASHINI_API_KEY=your_bhashini_api_key_here
BHASHINI_BASE_URL=https://bhashini.gov.in/api/v1
BHASHINI_TIMEOUT=10

# Voice Assets S3 Bucket
VOICE_ASSETS_BUCKET=trustgraph-voice-assets-production

# Database
DATABASE_PATH=trustgraph.db

# JWT Configuration
JWT_SECRET=your_secure_jwt_secret_here_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# UPI Gateway Configuration (stored in AWS Secrets Manager)
UPI_PAYMENTS_TABLE=trustgraph-upi-payments

# Blockchain Configuration
BLOCKCHAIN_NETWORK=trustgraph-fabric-network
BLOCKCHAIN_CHANNEL=indian-workforce-channel

# Application
ENVIRONMENT=production
PORT=8000
LOG_LEVEL=INFO
```

---

## Step 3: Deploy Infrastructure with CloudFormation

### Deploy the Stack
```bash
# Validate template
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation-stack.yaml \
  --region ap-south-1

# Create stack
aws cloudformation create-stack \
  --stack-name trustgraph-production \
  --template-body file://infrastructure/cloudformation-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=production \
    ParameterKey=DomainName,ParameterValue=trustgraph.gov.in \
    ParameterKey=CertificateArn,ParameterValue=arn:aws:acm:us-east-1:868422695661:certificate/your-cert-id \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-south-1

# Monitor stack creation
aws cloudformation wait stack-create-complete \
  --stack-name trustgraph-production \
  --region ap-south-1

# Get outputs
aws cloudformation describe-stacks \
  --stack-name trustgraph-production \
  --query 'Stacks[0].Outputs' \
  --region ap-south-1
```

---

## Step 4: Configure Bhashini API

### Register for Bhashini API
1. Visit: https://bhashini.gov.in/
2. Register for API access
3. Get API key for:
   - ASR (Automatic Speech Recognition)
   - NMT (Neural Machine Translation)
   - TTS (Text-to-Speech)

### Supported Languages
- Hindi (hi), Bengali (bn), Telugu (te), Marathi (mr)
- Tamil (ta), Gujarati (gu), Kannada (kn), Malayalam (ml)
- Odia (or), Punjabi (pa), Assamese (as), Urdu (ur)
- And 10 more constitutional languages

### Store API Key in AWS Secrets Manager
```bash
aws secretsmanager create-secret \
  --name trustgraph/bhashini/api-key \
  --secret-string '{"api_key":"your_bhashini_api_key"}' \
  --region ap-south-1
```

---

## Step 5: Configure UPI Payment Gateway

### Option A: Paytm Integration
```bash
aws secretsmanager create-secret \
  --name trustgraph/upi/gateway-config \
  --secret-string '{
    "primary_gateway": "paytm",
    "fallback_gateway": "phonepe",
    "merchant_id": "YOUR_PAYTM_MERCHANT_ID",
    "merchant_key": "YOUR_PAYTM_MERCHANT_KEY",
    "api_endpoints": {
      "paytm": "https://securegw.paytm.in/theia/api/v1/initiateTransaction",
      "phonepe": "https://api.phonepe.com/apis/hermes/pg/v1/pay"
    },
    "webhook_secret": "YOUR_WEBHOOK_SECRET",
    "timeout": 30
  }' \
  --region ap-south-1
```

### Option B: PhonePe Integration
Similar to Paytm, register at PhonePe Business and get credentials.

---

## Step 6: Setup Hyperledger Fabric Blockchain

### Using Amazon Managed Blockchain
```bash
# Create blockchain network
aws managedblockchain create-network \
  --name trustgraph-fabric-network \
  --framework HYPERLEDGER_FABRIC \
  --framework-version 2.2 \
  --framework-configuration '{
    "Fabric": {
      "Edition": "STANDARD"
    }
  }' \
  --voting-policy '{
    "ApprovalThresholdPolicy": {
      "ThresholdPercentage": 50,
      "ProposalDurationInHours": 24,
      "ThresholdComparator": "GREATER_THAN"
    }
  }' \
  --member-configuration '{
    "Name": "TrustGraphMember",
    "Description": "TrustGraph primary member",
    "FrameworkConfiguration": {
      "Fabric": {
        "AdminUsername": "admin",
        "AdminPassword": "YourSecurePassword123!"
      }
    }
  }' \
  --region ap-south-1
```

### Deploy Chaincode
```bash
# Package chaincode
cd blockchain/chaincode/trustledger
tar -czf trustledger.tar.gz .

# Install on peer nodes (follow AWS Managed Blockchain documentation)
```

---

## Step 7: Deploy Application

### Option A: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -c "from src.database import db; db.init_db()"

# Start application
python app.py
```

### Option B: AWS Lambda Deployment
```bash
# Package application
./deploy.sh

# Or use AWS SAM
sam build
sam deploy --guided
```

### Option C: Docker Deployment
```bash
# Build Docker image
docker build -t trustgraph-engine:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  trustgraph-engine:latest

# Or use docker-compose
docker-compose up -d
```

---

## Step 8: Deploy Frontend

### Build and Deploy to S3
```bash
# Get S3 bucket name from CloudFormation
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name trustgraph-production \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text \
  --region ap-south-1)

# Sync frontend files
aws s3 sync frontend/ s3://$BUCKET_NAME/ \
  --exclude "*.py" \
  --exclude "*.sh" \
  --exclude "*.bat" \
  --region ap-south-1

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name trustgraph-production \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text \
  --region ap-south-1)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

---

## Step 9: Verify Deployment

### Run Health Check
```bash
python system_health_check.py
```

### Expected Output
```
============================================================
TrustGraph Engine - System Health Check
============================================================

[1/5] Checking Database...
  ✅ All database tables present
  ✅ Database operational

[2/5] Checking Authentication Service...
  ✅ Auth service initialized
  ✅ OTP generation working

[3/5] Checking AWS Bedrock Service...
  ✅ Bedrock client initialized
  ✅ Intent classification working

[4/5] Checking API Endpoints...
  ✅ All required endpoints present

[5/5] Checking Frontend Configuration...
  ✅ All frontend files present

Overall Health: 100% (8/8 components)
```

### Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "aadhaar_number": "123456789012",
    "name": "Test User",
    "preferred_language": "hi"
  }'
```

---

## Step 10: Monitoring and Observability

### CloudWatch Dashboards
```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name TrustGraph-Production \
  --dashboard-body file://infrastructure/cloudwatch-dashboard.json \
  --region ap-south-1
```

### Set Up Alarms
- API Gateway 5xx errors > 10 in 5 minutes
- Lambda function errors > 5 in 5 minutes
- DynamoDB throttling events
- Bedrock API latency > 2 seconds

### X-Ray Tracing
Enable X-Ray for all Lambda functions to trace requests end-to-end.

---

## Troubleshooting

### Issue: Bedrock Access Denied
**Solution**: Verify IAM permissions (see Step 1)

### Issue: Voice Service Not Working
**Solution**: Check Bhashini API key in Secrets Manager

### Issue: Database Connection Errors
**Solution**: Verify database file permissions and path

### Issue: UPI Payments Failing
**Solution**: Verify gateway credentials in Secrets Manager

---

## Security Checklist

- [ ] All secrets stored in AWS Secrets Manager
- [ ] IAM roles follow least privilege principle
- [ ] S3 buckets have encryption enabled
- [ ] DynamoDB tables have point-in-time recovery
- [ ] CloudFront uses HTTPS only
- [ ] API Gateway has rate limiting
- [ ] Lambda functions have appropriate timeouts
- [ ] VPC endpoints for private AWS service access
- [ ] CloudWatch logs retention configured
- [ ] Backup and disaster recovery plan in place

---

## DPDP Act 2023 Compliance

### Data Residency
- All data stored in `ap-south-1` (Mumbai) region
- No cross-border data transfer without consent
- Disaster recovery in `ap-southeast-1` (Singapore) only

### User Rights
- Right to access personal data
- Right to correction
- Right to erasure
- Right to data portability

### Consent Management
- Explicit consent for data processing
- Granular consent for different purposes
- Easy consent withdrawal mechanism
- Consent records maintained for 7 years

---

## Performance Targets

- API response time: < 500ms (p95)
- Voice processing: < 2 seconds end-to-end
- Trust score calculation: < 1 second
- System availability: 99.9% uptime
- Concurrent users: 10M+ supported

---

## Cost Optimization

### Estimated Monthly Costs (1M users)
- Lambda: $500
- DynamoDB: $300
- S3 + CloudFront: $200
- Bedrock: $1,000
- Managed Blockchain: $2,000
- Total: ~$4,000/month

### Cost Reduction Strategies
- Use Lambda reserved concurrency for predictable workloads
- Enable DynamoDB auto-scaling
- Use S3 lifecycle policies for old data
- Implement caching with CloudFront
- Use Spot instances for batch processing

---

## Support and Maintenance

### Regular Tasks
- Weekly: Review CloudWatch logs and metrics
- Monthly: Security patches and updates
- Quarterly: Disaster recovery drills
- Annually: Compliance audits

### Contact
- Technical Support: tech@trustgraph.gov.in
- Security Issues: security@trustgraph.gov.in
- NITI Aayog Liaison: niti@trustgraph.gov.in

---

**Last Updated**: 2026-03-04
**Version**: 1.0.0
**Status**: Production Ready (62.5% → 100% after fixes)
