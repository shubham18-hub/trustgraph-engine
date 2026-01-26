---
inclusion: always
---

# TrustGraph Engine Development Standards

## Mission Context: Digital ShramSetu
This project implements NITI Aayog's Digital ShramSetu initiative to empower 490 million informal workers in India by converting social proof into bankable digital assets. All development decisions should align with this mission of financial inclusion and worker empowerment.

## Architecture Principles

### AWS-Native First
- **Serverless Priority**: Use AWS Lambda for all business logic to ensure scalability from pilot (1M users) to nationwide (490M users)
- **Managed Services**: Prefer managed AWS services over self-hosted solutions to minimize operational overhead
- **Multi-Region**: Design for ap-south-1 (Mumbai) primary with ap-southeast-1 (Singapore) disaster recovery

### Core AWS Services Stack
```yaml
compute: AWS Lambda (Python 3.11 runtime)
ai_ml: Amazon SageMaker (GraphStorm/DGL for GNN models)
database: Amazon Neptune (graph database for trust relationships)
storage: Amazon S3 (encrypted credential storage)
security: AWS KMS (cryptographic key management)
api: Amazon API Gateway (RESTful endpoints)
voice: Amazon Transcribe + Polly + Bhashini API
monitoring: CloudWatch + X-Ray for observability
```

## Technical Standards

### Backend Development (Python)
- **Runtime**: Python 3.11 for all Lambda functions
- **Framework**: FastAPI for API development with automatic OpenAPI documentation
- **Dependencies**: Use AWS SDK (boto3), cryptography library for W3C VC signing
- **Code Structure**: Domain-driven design with clear separation of concerns
- **Testing**: pytest with moto for AWS service mocking

### W3C Verifiable Credentials Compliance
- **Standard**: W3C Verifiable Credentials Data Model v1.1
- **Signature Suite**: Ed25519Signature2020 for cryptographic proofs
- **DID Method**: did:india: custom method for Indian context
- **JSON-LD Context**: Custom context for work credentials and skills
- **Verification**: Independent verification without centralized registry

### Voice-First UI Approach
- **Primary Interface**: Voice commands in 22 Indian languages via Bhashini API
- **Fallback UI**: Simple, high-contrast visual interface for confirmation/errors
- **Accessibility**: Screen reader compatible, large fonts, minimal cognitive load
- **Offline Capability**: Core functions available without internet connectivity

## Development Guidelines

### Code Organization
```
src/
├── handlers/           # Lambda function handlers
├── services/          # Business logic services
├── models/            # Data models and schemas
├── utils/             # Shared utilities
├── credentials/       # W3C VC implementation
└── voice/             # Voice interface logic

infrastructure/
├── cloudformation/    # AWS infrastructure as code
├── lambda_layers/     # Shared dependencies
└── deployment/        # CI/CD scripts
```

### Security Requirements
- **Encryption**: All data encrypted at rest (S3, Neptune) and in transit (TLS 1.3)
- **Authentication**: Aadhaar-based OTP + voice biometric secondary factor
- **Authorization**: JWT tokens with role-based access control
- **Privacy**: Self-sovereign identity - users control their data sharing
- **Compliance**: DPDP Act 2023, W3C DID standards, ISO 27001

### Performance Standards
- **API Response**: <500ms for standard operations
- **Voice Processing**: <2 seconds end-to-end for voice interactions
- **Trust Score**: <1 second for real-time credit score calculation
- **Scalability**: Auto-scaling to handle 10M+ concurrent users

### Data Standards
- **Verifiable Credentials**: JSON-LD format with cryptographic proofs
- **Graph Data**: Property graph model in Neptune for trust relationships
- **Voice Data**: Encrypted audio files in S3 with automatic transcription
- **Personal Data**: Minimal collection, explicit consent, automatic deletion

## Integration Patterns

### Government APIs
- **Aadhaar**: UIDAI Authentication API for identity verification
- **UPI**: NPCI integration for payment processing and transaction history
- **DigiLocker**: Document verification and storage integration

### Financial Services
- **Banking APIs**: Real-time trust score sharing with explicit user consent
- **Credit Scoring**: GNN-based alternative credit assessment
- **Payment Processing**: UPI integration for milestone-based payments

### Third-Party Services
- **Bhashini**: Multi-language voice processing and translation
- **Geolocation**: GPS verification for work location attestation
- **Document OCR**: Automated skill certificate verification

## Quality Assurance

### Testing Strategy
- **Unit Tests**: >90% code coverage for all business logic
- **Integration Tests**: End-to-end API testing with real AWS services
- **Load Testing**: Simulate 10M+ concurrent users using AWS Load Testing
- **Security Testing**: Regular penetration testing and vulnerability scans

### Monitoring & Observability
- **Metrics**: Business KPIs (credential issuance, trust scores) and technical metrics (latency, errors)
- **Logging**: Structured JSON logs with correlation IDs for request tracing
- **Alerting**: Real-time alerts for system health and security incidents
- **Dashboards**: CloudWatch dashboards for operational visibility

## Deployment Standards

### Environment Strategy
```
Development → Staging → Production
     ↓           ↓          ↓
   Single AZ   Multi-AZ   Multi-Region
```

### CI/CD Pipeline
- **Source Control**: Git with feature branch workflow
- **Build**: AWS CodeBuild with automated testing
- **Deploy**: AWS CodeDeploy with blue-green deployments
- **Infrastructure**: CloudFormation for infrastructure as code

### Cost Optimization
- **Serverless**: Pay-per-use Lambda functions to minimize idle costs
- **Storage Lifecycle**: Automatic S3 archival for old credentials
- **Reserved Capacity**: For predictable workloads like ML training
- **Monitoring**: Cost alerts and optimization recommendations

## Compliance & Governance

### Regulatory Compliance
- **Data Residency**: All Indian user data stored within India (ap-south-1)
- **Privacy Rights**: Right to access, correct, and delete personal data
- **Audit Trail**: Immutable blockchain logs for all credential operations
- **Consent Management**: Granular permissions for data sharing

### Code Quality
- **Linting**: Black formatter, flake8 linter, mypy type checking
- **Documentation**: Comprehensive docstrings and API documentation
- **Code Review**: Mandatory peer review for all changes
- **Security Scan**: Automated vulnerability scanning in CI/CD pipeline

---

*These standards ensure the TrustGraph Engine delivers on the Digital ShramSetu mission while maintaining security, scalability, and compliance with Indian regulations.*