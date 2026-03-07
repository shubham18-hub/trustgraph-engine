# TrustGraph Engine - Production Deployment Guide

## Overview
This guide covers deploying TrustGraph Engine to production on AWS infrastructure with high availability, security, and compliance with DPDP Act 2023.

## Prerequisites

### Required Tools
- AWS CLI v2.x configured with appropriate credentials
- Docker 20.x or later
- kubectl 1.28 or later (for Kubernetes deployment)
- Git
- Python 3.11

### AWS Account Setup
- AWS Account with appropriate permissions
- IAM roles configured for EKS, Lambda, DynamoDB
- ACM certificate for HTTPS (trustgraph.gov.in)
- Route53 hosted zone for domain management

## Deployment Options

### Option 1: Docker Compose (Simple Deployment)

Best for: Development, staging, or small-scale deployments

```bash
# 1. Clone repository
git clone https://github.com/your-org/trustgraph-engine.git
cd trustgraph-engine

# 2. Configure environment
cp .env.example .env.production
# Edit .env.production with your credentials

# 3. Build and start services
docker-compose up -d

# 4. Verify deployment
curl http://localhost:8000/api/health
```

### Option 2: AWS CloudFormation (Serverless)

Best for: Production with auto-scaling and managed services

```bash
# 1. Configure AWS credentials
aws configure

# 2. Deploy infrastructure
./deploy.sh production ap-south-1

# 3. Verify deployment
aws cloudformation describe-stacks --stack-name trustgraph-production
```

### Option 3: Kubernetes on EKS (Enterprise)

Best for: Large-scale production with full control

```bash
# 1. Create EKS cluster (if not exists)
eksctl create cluster \
  --name trustgraph-production \
  --region ap-south-1 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed

# 2. Configure kubectl
aws eks update-kubeconfig --name trustgraph-production --region ap-south-1

# 3. Deploy application
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/ingress.yaml

# 4. Verify deployment
kubectl get pods -n trustgraph
kubectl get svc -n trustgraph
```

## Configuration

### Environment Variables

Critical environment variables that must be configured:

```bash
# Security (REQUIRED)
JWT_SECRET_KEY=<generate-strong-secret>
ENCRYPTION_KEY=<32-byte-encryption-key>

# AWS Services (REQUIRED)
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=<your-account-id>

# API Keys (REQUIRED)
BHASHINI_API_KEY=<your-bhashini-key>
AADHAAR_API_KEY=<your-aadhaar-key>
UPI_MERCHANT_ID=<your-merchant-id>

# Database
DATABASE_PATH=/app/data/trustgraph.db

# Redis
REDIS_PASSWORD=<strong-password>
```

### Secrets Management

Store sensitive credentials in AWS Secrets Manager:

```bash
# Create secrets
aws secretsmanager create-secret \
  --name trustgraph/production/jwt-secret \
  --secret-string "your-jwt-secret" \
  --region ap-south-1

aws secretsmanager create-secret \
  --name trustgraph/production/encryption-key \
  --secret-string "your-encryption-key" \
  --region ap-south-1
```

## Security Hardening

### 1. Network Security

```bash
# Configure security groups
aws ec2 create-security-group \
  --group-name trustgraph-api \
  --description "TrustGraph API security group" \
  --vpc-id <your-vpc-id>

# Allow HTTPS only
aws ec2 authorize-security-group-ingress \
  --group-id <sg-id> \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 2. IAM Policies

Minimum required IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-south-1:*:table/trustgraph-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt"
      ],
      "Resource": "arn:aws:kms:ap-south-1:*:key/*"
    }
  ]
}
```

### 3. SSL/TLS Configuration

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name trustgraph.gov.in \
  --subject-alternative-names "*.trustgraph.gov.in" \
  --validation-method DNS \
  --region ap-south-1
```

## Monitoring & Observability

### CloudWatch Dashboards

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name TrustGraph-Production \
  --dashboard-body file://monitoring/dashboard.json
```

### Alarms

```bash
# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name trustgraph-api-5xx \
  --alarm-description "API Gateway 5xx errors" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### Log Aggregation

```bash
# Create log group
aws logs create-log-group \
  --log-group-name /aws/trustgraph/production \
  --region ap-south-1

# Set retention
aws logs put-retention-policy \
  --log-group-name /aws/trustgraph/production \
  --retention-in-days 30
```

## Backup & Disaster Recovery

### Automated Backups

```bash
# Schedule daily backups (cron)
0 2 * * * /app/scripts/backup.sh

# Or use AWS Backup
aws backup create-backup-plan \
  --backup-plan file://backup-plan.json
```

### Restore Procedure

```bash
# List available backups
aws s3 ls s3://trustgraph-backups-production/

# Restore from backup
./scripts/restore.sh trustgraph-backup-20260304_020000
```

### Multi-Region Failover

```bash
# Deploy to secondary region
./deploy.sh production ap-southeast-1

# Configure Route53 health checks
aws route53 create-health-check \
  --health-check-config file://health-check-config.json
```

## Performance Optimization

### Auto-Scaling Configuration

```bash
# Configure EKS auto-scaling
kubectl apply -f kubernetes/deployment.yaml
# HPA is included in deployment.yaml

# Verify HPA
kubectl get hpa -n trustgraph
```

### Database Optimization

```bash
# Enable DynamoDB auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id "table/trustgraph-users-production" \
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" \
  --min-capacity 5 \
  --max-capacity 100
```

### CDN Configuration

CloudFront is automatically configured via CloudFormation. To invalidate cache:

```bash
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/*"
```

## Health Checks

### Manual Health Check

```bash
# Run health check script
./scripts/health-check.sh

# Or check endpoints directly
curl https://api.trustgraph.gov.in/api/health
```

### Automated Monitoring

```bash
# Set up cron job for continuous monitoring
*/5 * * * * /app/scripts/health-check.sh >> /var/log/health-check.log 2>&1
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database file permissions
   ls -la /app/data/trustgraph.db
   
   # Verify database integrity
   sqlite3 /app/data/trustgraph.db "PRAGMA integrity_check;"
   ```

2. **AWS Service Errors**
   ```bash
   # Verify IAM permissions
   aws sts get-caller-identity
   
   # Test Bedrock access
   aws bedrock list-foundation-models --region ap-south-1
   ```

3. **High Memory Usage**
   ```bash
   # Check container stats
   docker stats trustgraph-backend
   
   # Restart service
   docker-compose restart backend
   ```

### Logs Access

```bash
# Docker logs
docker logs trustgraph-backend --tail 100 -f

# Kubernetes logs
kubectl logs -f deployment/trustgraph-backend -n trustgraph

# CloudWatch logs
aws logs tail /aws/trustgraph/production --follow
```

## Compliance & Auditing

### DPDP Act 2023 Compliance

- All data stored in ap-south-1 (Mumbai) region
- Encryption at rest and in transit
- Audit logs enabled for all data access
- User consent management implemented

### Audit Reports

```bash
# Generate compliance report
python scripts/generate_compliance_report.py --period monthly

# Export audit logs
aws logs filter-log-events \
  --log-group-name /aws/trustgraph/production \
  --start-time $(date -d '30 days ago' +%s)000 \
  --output json > audit-logs.json
```

## Rollback Procedure

### Quick Rollback

```bash
# Docker Compose
docker-compose down
git checkout <previous-commit>
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/trustgraph-backend -n trustgraph

# CloudFormation
aws cloudformation update-stack \
  --stack-name trustgraph-production \
  --use-previous-template
```

## Maintenance Windows

### Planned Maintenance

```bash
# 1. Enable maintenance mode
kubectl scale deployment trustgraph-backend --replicas=0 -n trustgraph

# 2. Perform maintenance
./scripts/backup.sh
# Run database migrations, updates, etc.

# 3. Disable maintenance mode
kubectl scale deployment trustgraph-backend --replicas=3 -n trustgraph
```

## Support & Escalation

### Contact Information
- Technical Support: tech-support@trustgraph.gov.in
- Security Issues: security@trustgraph.gov.in
- NITI Aayog Liaison: niti-liaison@trustgraph.gov.in

### Emergency Procedures
1. Critical security issue: Immediately scale down and notify security team
2. Data breach: Follow DPDP Act incident response (notify within 72 hours)
3. Service outage: Activate disaster recovery in ap-southeast-1

## Post-Deployment Checklist

- [ ] All environment variables configured
- [ ] SSL certificates installed and valid
- [ ] Database backups scheduled
- [ ] Monitoring and alerts configured
- [ ] Health checks passing
- [ ] Security scan completed
- [ ] Load testing performed
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Incident response plan reviewed

## Next Steps

1. Configure custom domain in Route53
2. Set up CI/CD pipeline for automated deployments
3. Enable AWS WAF for additional security
4. Configure CloudWatch dashboards
5. Schedule regular security audits
6. Plan capacity for scaling to 490M users

---

For detailed AWS service configuration, see `DEPLOYMENT_GUIDE.md`
For development setup, see `README.md`
For API documentation, see `API.md`
