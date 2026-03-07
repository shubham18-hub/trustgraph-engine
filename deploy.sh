#!/bin/bash
set -e

# TrustGraph Engine - AWS Deployment Script
# Supports multi-region failover and high availability

ENVIRONMENT=${1:-production}
AWS_REGION=${2:-ap-south-1}
STACK_NAME="trustgraph-${ENVIRONMENT}"

echo "=========================================="
echo "TrustGraph Engine - AWS Deployment"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "Stack: $STACK_NAME"
echo "=========================================="

# Step 1: Build Frontend
echo "[1/7] Building frontend..."
cd frontend
npm install --production 2>/dev/null || echo "No npm dependencies"

# Minify CSS
echo "Minifying CSS..."
cat styles.css themes.css accessibility.css > dist/bundle.css

# Minify JS
echo "Minifying JavaScript..."
cat app.js voice.js > dist/bundle.js

# Copy HTML
cp index.html dist/
cp theme-config.json dist/

cd ..

# Step 2: Deploy CloudFormation Stack
echo "[2/7] Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation-stack.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides Environment=$ENVIRONMENT \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

# Get stack outputs
echo "Getting stack outputs..."
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text \
  --region $AWS_REGION)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text \
  --region $AWS_REGION)

API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text \
  --region $AWS_REGION)

echo "Bucket: $BUCKET_NAME"
echo "Distribution: $DISTRIBUTION_ID"
echo "API: $API_ENDPOINT"

# Step 3: Upload Frontend to S3
echo "[3/7] Uploading frontend to S3..."
aws s3 sync frontend/dist s3://$BUCKET_NAME/ \
  --delete \
  --cache-control "public, max-age=31536000" \
  --region $AWS_REGION

# Upload HTML with no-cache
aws s3 cp frontend/dist/index.html s3://$BUCKET_NAME/index.html \
  --cache-control "no-cache" \
  --content-type "text/html" \
  --region $AWS_REGION

# Step 4: Invalidate CloudFront Cache
echo "[4/7] Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*" \
  --region $AWS_REGION

# Step 5: Deploy Lambda Functions
echo "[5/7] Deploying Lambda functions..."

# Package Lambda functions
cd src
zip -r ../lambda-auth.zip services/auth_service.py core/ -q
zip -r ../lambda-voice.zip services/voice_service.py services/bedrock_service.py core/ -q
cd ..

# Update Lambda functions
aws lambda update-function-code \
  --function-name trustgraph-auth-$ENVIRONMENT \
  --zip-file fileb://lambda-auth.zip \
  --region $AWS_REGION

aws lambda update-function-code \
  --function-name trustgraph-voice-$ENVIRONMENT \
  --zip-file fileb://lambda-voice.zip \
  --region $AWS_REGION

# Cleanup
rm lambda-auth.zip lambda-voice.zip

# Step 6: Configure API Gateway Routes
echo "[6/7] Configuring API Gateway..."
# Routes are configured via CloudFormation

# Step 7: Health Check
echo "[7/7] Running health check..."
sleep 10

HEALTH_URL="${API_ENDPOINT}/health"
echo "Checking: $HEALTH_URL"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $HTTP_CODE -eq 200 ]; then
  echo "✓ Health check passed"
else
  echo "✗ Health check failed (HTTP $HTTP_CODE)"
  exit 1
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Frontend URL: https://$DISTRIBUTION_ID.cloudfront.net"
echo "API Endpoint: $API_ENDPOINT"
echo "=========================================="
