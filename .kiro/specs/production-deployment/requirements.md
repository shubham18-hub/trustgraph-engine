# TrustGraph Engine - Production Deployment & Infrastructure Requirements

## Mission Context
Deploy a production-ready, scalable infrastructure for the TrustGraph Engine to serve 490 million informal workers across India, ensuring DPDP Act 2023 compliance, multi-region resilience, and voice-first accessibility.

## 1. AWS Infrastructure Setup & Configuration

### 1.1 Multi-Region Architecture

#### FR-INFRA-001: Primary Region Deployment (ap-south-1 Mumbai)
**Priority**: Critical  
**DPDP Act Requirement**: All Indian citizen data MUST reside in India

**Acceptance Criteria**:
- All Lambda functions MUST be deployed in ap-south-1 region
- DynamoDB tables MUST have point-in-time recovery enabled
- S3 buckets MUST have versioning and encryption enabled
- Neptune graph database MUST be deployed in Multi-AZ configuration
- All data at rest MUST be encrypted using AWS KMS keys in ap-south-1
- CloudFront distributions MUST use ap-south-1 as origin
- No data replication outside India without explicit government approval

**Technical Specification**:
```yaml
primary_region: ap-south-1
availability_zones: [ap-south-1a, ap-south-1b, ap-south-1c]
data_residency: INDIA_ONLY
compliance: DPDP_ACT_2023
```

#### FR-INFRA-002: Disaster Recovery Region (ap-southeast-1 Singapore)
**Priority**: High  
**Purpose**: Business continuity only, no active data processing

**Acceptance Criteria**:
- DR region MUST only store encrypted backups
- Failover MUST be manual with government notification
- Recovery Time Objective (RTO) MUST be < 4 hours
- Recovery Point Objective (RPO) MUST be < 1 hour
- DR testing MUST be conducted quarterly

**Technical Specification**:
```yaml
dr_region: ap-southeast-1
backup_frequency: hourly
encryption: AES-256-GCM
failover_type: manual
notification_required: [NITI_AAYOG, MeitY, Data_Protection_Board]
```

### 1.2 Serverless Compute Infrastructure

#### FR-INFRA-003: AWS Lambda Configuration
**Priority**: Critical  
**Scale Target**: 10M+ concurrent users

**Acceptance Criteria**:
- All Lambda functions MUST use Python 3.11 runtime
- Reserved concurrency MUST be configured for critical functions
- Provisioned concurrency MUST be enabled for voice processing (min 100 instances)
- Memory allocation MUST be optimized per function (512MB-3GB range)
- Timeout MUST be set appropriately (voice: 30s, API: 15s, batch: 900s)
- Dead Letter Queues (DLQ) MUST be configured for all async functions
- X-Ray tracing MUST be enabled for all functions
- Environment variables MUST be encrypted using KMS

**Lambda Functions Inventory**:
```python
functions = {
    "voice-processor": {
        "memory": 1024,
        "timeout": 30,
        "concurrency": "provisioned:100",
        "layers": ["bhashini-sdk", "audio-processing"],
        "vpc": False  # Public internet access for Bhashini API
    },
    "auth-handler": {
        "memory": 512,
        "timeout": 15,
        "concurrency": "reserved:500",
        "layers": ["cryptography", "jwt"],
        "vpc": True  # Access to Neptune and DynamoDB
    },
    "credential-issuer": {
        "memory": 1024,
        "timeout": 30,
        "concurrency": "reserved:200",
        "layers": ["blockchain-sdk", "w3c-vc"],
        "vpc": True
    },
    "trust-score-calculator": {
        "memory": 2048,
        "timeout": 15,
        "concurrency": "provisioned:50",
        "layers": ["graphstorm", "numpy"],
        "vpc": True
    },
    "payment-processor": {
        "memory": 512,
        "timeout": 30,
        "concurrency": "reserved:300",
        "layers": ["upi-sdk"],
        "vpc": True
    }
}
```


#### FR-INFRA-004: Lambda Layers Management
**Priority**: High  
**Purpose**: Reduce deployment package size and improve cold start times

**Acceptance Criteria**:
- Common dependencies MUST be packaged as Lambda layers
- Layer versions MUST be immutable and versioned
- Maximum 5 layers per function (AWS limit)
- Layer size MUST be optimized (< 50MB per layer)
- Layers MUST be region-specific (ap-south-1)

**Layer Structure**:
```
lambda_layers/
├── bhashini-dependencies/
│   ├── python/
│   │   └── lib/python3.11/site-packages/
│   │       ├── aiohttp/
│   │       ├── requests/
│   │       └── bhashini_sdk/
├── blockchain-dependencies/
│   ├── python/
│   │   └── lib/python3.11/site-packages/
│   │       ├── fabric_sdk/
│   │       ├── cryptography/
│   │       └── w3c_vc/
├── ml-dependencies/
│   ├── python/
│   │   └── lib/python3.11/site-packages/
│   │       ├── torch/
│   │       ├── dgl/
│   │       └── graphstorm/
└── common-utilities/
    ├── python/
    │   └── lib/python3.11/site-packages/
    │       ├── boto3/
    │       ├── pydantic/
    │       └── fastapi/
```

### 1.3 Database Infrastructure

#### FR-INFRA-005: Amazon DynamoDB Configuration
**Priority**: Critical  
**Purpose**: High-performance NoSQL for user data and sessions

**Acceptance Criteria**:
- All tables MUST use on-demand billing mode for auto-scaling
- Point-in-time recovery MUST be enabled for all tables
- Encryption at rest MUST use AWS KMS customer-managed keys
- Global Secondary Indexes (GSI) MUST be optimized for query patterns
- DynamoDB Streams MUST be enabled for audit logging
- Backup retention MUST be 35 days minimum
- Cross-region replication MUST be disabled (DPDP compliance)

**Table Schema**:
```python
tables = {
    "trustgraph-users": {
        "partition_key": "user_id",
        "sort_key": None,
        "gsi": [
            {"name": "phone-index", "pk": "phone", "sk": None},
            {"name": "aadhaar-hash-index", "pk": "aadhaar_hash", "sk": None}
        ],
        "attributes": [
            "user_id", "phone", "aadhaar_hash", "name", "email",
            "preferred_language", "kyc_status", "created_at", "last_login"
        ],
        "ttl_attribute": None,
        "stream": "NEW_AND_OLD_IMAGES"
    },
    "trustgraph-credentials": {
        "partition_key": "credential_id",
        "sort_key": None,
        "gsi": [
            {"name": "worker-index", "pk": "worker_id", "sk": "issued_at"},
            {"name": "employer-index", "pk": "employer_id", "sk": "issued_at"}
        ],
        "attributes": [
            "credential_id", "worker_id", "employer_id", "work_type",
            "issued_at", "expires_at", "blockchain_tx_id", "status"
        ],
        "ttl_attribute": "expires_at",
        "stream": "NEW_AND_OLD_IMAGES"
    },
    "trustgraph-sessions": {
        "partition_key": "session_id",
        "sort_key": None,
        "gsi": [
            {"name": "user-index", "pk": "user_id", "sk": "created_at"}
        ],
        "attributes": [
            "session_id", "user_id", "token", "created_at", "expires_at"
        ],
        "ttl_attribute": "expires_at",
        "stream": None
    },
    "trustgraph-otps": {
        "partition_key": "phone",
        "sort_key": "created_at",
        "gsi": None,
        "attributes": [
            "phone", "otp", "created_at", "expires_at", "verified"
        ],
        "ttl_attribute": "expires_at",
        "stream": None
    }
}
```


#### FR-INFRA-006: Amazon Neptune Graph Database
**Priority**: Critical  
**Purpose**: Store trust graph for GNN-based credit scoring

**Acceptance Criteria**:
- Neptune cluster MUST be deployed in Multi-AZ configuration
- Instance type MUST be db.r5.xlarge minimum (4 vCPU, 32GB RAM)
- Read replicas MUST be configured (minimum 2 replicas)
- Automated backups MUST be enabled with 35-day retention
- Encryption at rest MUST use KMS customer-managed keys
- VPC security groups MUST restrict access to Lambda functions only
- Query timeout MUST be set to 120 seconds
- Audit logging MUST be enabled to CloudWatch

**Neptune Configuration**:
```yaml
cluster_configuration:
  engine: neptune
  engine_version: "1.2.1.0"
  instance_class: db.r5.xlarge
  instances: 3  # 1 writer + 2 readers
  multi_az: true
  vpc_security_groups: [sg-lambda-access-only]
  
backup_configuration:
  automated_backups: true
  backup_retention_period: 35
  preferred_backup_window: "03:00-04:00"  # IST 8:30-9:30 AM
  
encryption:
  storage_encrypted: true
  kms_key_id: "arn:aws:kms:ap-south-1:ACCOUNT:key/KEY_ID"
  
monitoring:
  cloudwatch_logs_exports: [audit]
  enhanced_monitoring: true
  monitoring_interval: 60
```

### 1.4 Storage Infrastructure

#### FR-INFRA-007: Amazon S3 Bucket Configuration
**Priority**: Critical  
**Purpose**: Store voice recordings, credentials, and static assets

**Acceptance Criteria**:
- All buckets MUST have versioning enabled
- Server-side encryption MUST use KMS customer-managed keys
- Bucket policies MUST enforce encryption in transit (TLS 1.3)
- Lifecycle policies MUST be configured for cost optimization
- Access logging MUST be enabled to audit bucket
- Public access MUST be blocked for all buckets
- CORS MUST be configured for frontend access
- Object Lock MUST be enabled for compliance data

**S3 Bucket Structure**:
```python
buckets = {
    "trustgraph-voice-recordings": {
        "purpose": "Store encrypted voice audio files",
        "encryption": "aws:kms",
        "versioning": True,
        "lifecycle_rules": [
            {"transition_to_ia": 30, "transition_to_glacier": 90, "expiration": 365}
        ],
        "cors": True,
        "public_access": False,
        "object_lock": False
    },
    "trustgraph-credentials": {
        "purpose": "Store W3C Verifiable Credentials",
        "encryption": "aws:kms",
        "versioning": True,
        "lifecycle_rules": [
            {"transition_to_ia": 90, "transition_to_glacier": 365}
        ],
        "cors": False,
        "public_access": False,
        "object_lock": True  # Compliance requirement
    },
    "trustgraph-frontend-assets": {
        "purpose": "Static website hosting",
        "encryption": "aws:kms",
        "versioning": True,
        "lifecycle_rules": [],
        "cors": True,
        "public_access": True,  # Via CloudFront only
        "object_lock": False
    },
    "trustgraph-ml-models": {
        "purpose": "Store trained GNN models",
        "encryption": "aws:kms",
        "versioning": True,
        "lifecycle_rules": [
            {"transition_to_ia": 30}
        ],
        "cors": False,
        "public_access": False,
        "object_lock": False
    },
    "trustgraph-audit-logs": {
        "purpose": "Compliance and audit logs",
        "encryption": "aws:kms",
        "versioning": True,
        "lifecycle_rules": [
            {"transition_to_glacier": 90}
        ],
        "cors": False,
        "public_access": False,
        "object_lock": True  # Immutable logs
    }
}
```


## 2. Voice Interface & Multilingual Support

### 2.1 Bhashini API Integration

#### FR-VOICE-001: Primary Voice Processing Pipeline
**Priority**: Critical  
**Languages**: 22 constitutional languages of India

**Acceptance Criteria**:
- Bhashini API MUST be primary voice processing service
- API calls MUST have 10-second timeout with retry logic
- Voice recognition accuracy MUST be >95% for common work vocabulary
- System MUST support real-time streaming for voice input
- Fallback to AWS Transcribe MUST be automatic on Bhashini failure
- Voice processing latency MUST be <2 seconds end-to-end
- All voice data MUST be encrypted in transit and at rest

**Supported Languages**:
```python
bhashini_languages = {
    "tier_1_high_usage": [
        {"code": "hi", "name": "Hindi", "speakers": "528M"},
        {"code": "bn", "name": "Bengali", "speakers": "265M"},
        {"code": "te", "name": "Telugu", "speakers": "93M"},
        {"code": "mr", "name": "Marathi", "speakers": "83M"},
        {"code": "ta", "name": "Tamil", "speakers": "77M"}
    ],
    "tier_2_medium_usage": [
        {"code": "gu", "name": "Gujarati", "speakers": "56M"},
        {"code": "kn", "name": "Kannada", "speakers": "44M"},
        {"code": "ml", "name": "Malayalam", "speakers": "38M"},
        {"code": "or", "name": "Odia", "speakers": "38M"},
        {"code": "pa", "name": "Punjabi", "speakers": "33M"}
    ],
    "tier_3_regional": [
        {"code": "as", "name": "Assamese", "speakers": "15M"},
        {"code": "ur", "name": "Urdu", "speakers": "51M"},
        {"code": "ne", "name": "Nepali", "speakers": "3M"},
        {"code": "ks", "name": "Kashmiri", "speakers": "7M"},
        {"code": "sd", "name": "Sindhi", "speakers": "3M"},
        {"code": "mai", "name": "Maithili", "speakers": "13M"},
        {"code": "bho", "name": "Bhojpuri", "speakers": "51M"},
        {"code": "gom", "name": "Konkani", "speakers": "2.5M"},
        {"code": "mni", "name": "Manipuri", "speakers": "1.8M"},
        {"code": "sat", "name": "Santali", "speakers": "7M"},
        {"code": "doi", "name": "Dogri", "speakers": "2.6M"},
        {"code": "brx", "name": "Bodo", "speakers": "1.4M"}
    ]
}
```

#### FR-VOICE-002: AWS Transcribe/Polly Fallback
**Priority**: High  
**Purpose**: Ensure 99.9% voice service availability

**Acceptance Criteria**:
- AWS Transcribe MUST support Hindi, Bengali, Tamil, Telugu, Marathi
- Automatic fallback MUST trigger within 3 seconds of Bhashini timeout
- Fallback usage MUST be logged for monitoring
- Voice quality MUST be maintained in fallback mode
- Cost optimization MUST prefer Bhashini over AWS services

**Fallback Logic**:
```python
async def process_voice_with_fallback(audio_data, language, user_context):
    """
    Voice processing with automatic fallback
    """
    try:
        # Primary: Bhashini API
        result = await bhashini_client.transcribe(
            audio_data=audio_data,
            source_language=language,
            timeout=10
        )
        
        if result['confidence'] > 0.8:
            return {
                'text': result['transcription'],
                'confidence': result['confidence'],
                'service': 'bhashini',
                'fallback_used': False
            }
    except (TimeoutError, BhashiniAPIError) as e:
        logger.warning(f"Bhashini failed: {e}, using AWS fallback")
    
    # Fallback: AWS Transcribe
    result = await aws_transcribe_client.transcribe(
        audio_data=audio_data,
        language_code=map_to_aws_language(language)
    )
    
    return {
        'text': result['transcription'],
        'confidence': result['confidence'],
        'service': 'aws_transcribe',
        'fallback_used': True
    }
```


### 2.2 Voice Intent Classification

#### FR-VOICE-003: Indian Work Context Understanding
**Priority**: Critical  
**Purpose**: Accurately classify worker intents in regional languages

**Acceptance Criteria**:
- System MUST recognize 50+ work-related intents
- Intent classification accuracy MUST be >90%
- Regional variations MUST be supported (e.g., "राजमिस्त्री" vs "கொத்தனார்")
- Context awareness MUST improve accuracy over time
- Ambiguous intents MUST trigger clarification prompts

**Intent Categories**:
```python
voice_intents = {
    "milestone_completion": {
        "patterns": {
            "hi": ["काम पूरा", "काम खत्म", "कार्य समाप्त"],
            "ta": ["வேலை முடிந்தது", "பணி நிறைவு"],
            "bn": ["কাজ শেষ", "কার্য সম্পন্ন"],
            "te": ["పని పూర్తి", "కార్యం ముగిసింది"]
        },
        "required_entities": ["work_type", "completion_percentage"],
        "next_action": "request_photo_evidence"
    },
    "payment_inquiry": {
        "patterns": {
            "hi": ["पैसा कब", "भुगतान कब", "पेमेंट स्टेटस"],
            "ta": ["பணம் எப்போது", "சம்பளம் எப்போது"],
            "bn": ["টাকা কবে", "বেতন কবে"],
            "te": ["డబ్బు ఎప్పుడు", "చెల్లింపు ఎప్పుడు"]
        },
        "required_entities": ["milestone_id"],
        "next_action": "check_payment_status"
    },
    "trust_score_check": {
        "patterns": {
            "hi": ["ट्रस्ट स्कोर", "क्रेडिट स्कोर", "मेरा स्कोर"],
            "ta": ["நம்பிக்கை மதிப்பெண்", "கடன் மதிப்பெண்"],
            "bn": ["বিশ্বাস স্কোর", "ক্রেডিট স্কোর"],
            "te": ["ట్రస్ట్ స్కోర్", "క్రెడిట్ స్కోర్"]
        },
        "required_entities": [],
        "next_action": "calculate_and_return_score"
    },
    "skill_verification": {
        "patterns": {
            "hi": ["हुनर सत्यापन", "स्किल वेरिफाई", "प्रमाणपत्र"],
            "ta": ["திறமை சரிபார்ப்பு", "சான்றிதழ்"],
            "bn": ["দক্ষতা যাচাই", "সার্টিফিকেট"],
            "te": ["నైపుణ్యం ధృవీకరణ", "సర్టిఫికేట్"]
        },
        "required_entities": ["skill_name"],
        "next_action": "initiate_skill_verification"
    }
}
```

## 3. Authentication & Security Implementation

### 3.1 Aadhaar-Based Authentication

#### FR-AUTH-001: UIDAI Integration
**Priority**: Critical  
**Compliance**: DPDP Act 2023, Aadhaar Act 2016

**Acceptance Criteria**:
- Aadhaar numbers MUST NEVER be stored in plain text
- Only SHA-256 irreversible hash MUST be stored
- UIDAI OTP authentication MUST be primary method
- Consent MUST be obtained before Aadhaar verification
- Aadhaar data MUST be used only for identity verification
- Integration MUST use UIDAI's official API endpoints
- All Aadhaar operations MUST be logged for audit

**Implementation**:
```python
class AadhaarAuthService:
    """
    DPDP Act 2023 compliant Aadhaar authentication
    """
    
    def __init__(self):
        self.uidai_endpoint = os.getenv('UIDAI_API_ENDPOINT')
        self.agency_code = os.getenv('UIDAI_AGENCY_CODE')
        self.kms_client = boto3.client('kms', region_name='ap-south-1')
    
    def hash_aadhaar(self, aadhaar_number: str) -> str:
        """
        Create irreversible hash of Aadhaar number
        DPDP Act requirement: No plain text storage
        """
        # Remove spaces and validate format
        aadhaar = aadhaar_number.replace(' ', '').replace('-', '')
        
        if not self._validate_aadhaar_format(aadhaar):
            raise ValueError("Invalid Aadhaar format")
        
        # Create SHA-256 hash with salt
        salt = os.getenv('AADHAAR_HASH_SALT')
        hash_input = f"{aadhaar}{salt}".encode()
        aadhaar_hash = hashlib.sha256(hash_input).hexdigest()
        
        # Log operation for audit (without Aadhaar number)
        self._audit_log("aadhaar_hash_created", {
            "hash": aadhaar_hash[:8] + "...",  # Partial hash for tracking
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return aadhaar_hash
    
    async def initiate_otp_auth(self, aadhaar_number: str, consent: bool) -> dict:
        """
        Initiate UIDAI OTP authentication
        """
        if not consent:
            raise ValueError("User consent required for Aadhaar authentication")
        
        # Hash Aadhaar for internal tracking
        aadhaar_hash = self.hash_aadhaar(aadhaar_number)
        
        # Call UIDAI API to send OTP
        response = await self._call_uidai_api(
            endpoint="/otp/generate",
            payload={
                "aadhaar": aadhaar_number,
                "agency_code": self.agency_code,
                "consent": "Y"
            }
        )
        
        return {
            "transaction_id": response['txn_id'],
            "aadhaar_hash": aadhaar_hash,
            "otp_sent": True,
            "expires_in": 300  # 5 minutes
        }
```


#### FR-AUTH-002: Multi-Factor Authentication
**Priority**: Critical  
**Purpose**: Enhanced security with voice biometric as second factor

**Acceptance Criteria**:
- Primary authentication MUST be Aadhaar OTP
- Secondary authentication MUST be voice biometric (optional)
- Voice biometric patterns MUST be stored as irreversible hashes
- MFA MUST be required for sensitive operations (credential sharing, payment)
- Biometric data MUST comply with DPDP Act privacy requirements
- Users MUST be able to disable voice biometric authentication

**Voice Biometric Flow**:
```python
class VoiceBiometricAuth:
    """
    Voice biometric authentication as second factor
    """
    
    async def enroll_voice_biometric(self, user_id: str, voice_samples: List[bytes]) -> dict:
        """
        Enroll user's voice biometric pattern
        Requires 3-5 voice samples for accuracy
        """
        # Extract voice features using AWS Transcribe
        voice_features = []
        for sample in voice_samples:
            features = await self._extract_voice_features(sample)
            voice_features.append(features)
        
        # Create voice signature (irreversible hash)
        voice_signature = self._create_voice_signature(voice_features)
        
        # Store encrypted signature in DynamoDB
        await self._store_voice_signature(user_id, voice_signature)
        
        return {
            "enrolled": True,
            "user_id": user_id,
            "samples_processed": len(voice_samples),
            "confidence": 0.95
        }
    
    async def verify_voice_biometric(self, user_id: str, voice_sample: bytes) -> dict:
        """
        Verify user's voice against enrolled pattern
        """
        # Extract features from current sample
        current_features = await self._extract_voice_features(voice_sample)
        
        # Retrieve stored voice signature
        stored_signature = await self._get_voice_signature(user_id)
        
        # Compare signatures
        similarity_score = self._compare_voice_signatures(
            current_features, 
            stored_signature
        )
        
        # Threshold for verification
        verified = similarity_score > 0.85
        
        return {
            "verified": verified,
            "confidence": similarity_score,
            "user_id": user_id
        }
```

### 3.2 JWT Token Management

#### FR-AUTH-003: Secure Token Generation and Validation
**Priority**: Critical  
**Purpose**: Stateless authentication for API access

**Acceptance Criteria**:
- JWT tokens MUST use RS256 algorithm (asymmetric encryption)
- Private keys MUST be stored in AWS Secrets Manager
- Token expiry MUST be 15 minutes for access tokens
- Refresh tokens MUST be valid for 7 days
- Token rotation MUST be automatic on refresh
- Revoked tokens MUST be tracked in DynamoDB
- All token operations MUST be logged for audit

**JWT Implementation**:
```python
class JWTTokenManager:
    """
    Secure JWT token management with AWS Secrets Manager
    """
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager', region_name='ap-south-1')
        self.private_key = self._get_private_key()
        self.public_key = self._get_public_key()
    
    def generate_access_token(self, user_id: str, role: str, metadata: dict = None) -> str:
        """
        Generate short-lived access token
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'jti': secrets.token_urlsafe(16),  # Unique token ID
            'iss': 'trustgraph.gov.in',
            'aud': 'trustgraph-api'
        }
        
        if metadata:
            payload['metadata'] = metadata
        
        token = jwt.encode(payload, self.private_key, algorithm='RS256')
        
        # Log token generation
        self._audit_log('token_generated', {
            'user_id': user_id,
            'token_id': payload['jti'],
            'expires_at': payload['exp'].isoformat()
        })
        
        return token
    
    def generate_refresh_token(self, user_id: str) -> str:
        """
        Generate long-lived refresh token
        """
        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=7),
            'jti': secrets.token_urlsafe(32)
        }
        
        token = jwt.encode(payload, self.private_key, algorithm='RS256')
        
        # Store refresh token in DynamoDB for revocation tracking
        self._store_refresh_token(user_id, payload['jti'], payload['exp'])
        
        return token
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=['RS256'],
                issuer='trustgraph.gov.in',
                audience='trustgraph-api'
            )
            
            # Check if token is revoked
            if self._is_token_revoked(payload['jti']):
                raise ValueError('Token has been revoked')
            
            return {
                'valid': True,
                'user_id': payload['user_id'],
                'role': payload.get('role'),
                'metadata': payload.get('metadata', {})
            }
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            return {'valid': False, 'error': str(e)}
```

### 3.3 API Security

#### FR-AUTH-004: API Gateway Security Configuration
**Priority**: Critical  
**Purpose**: Protect APIs from unauthorized access and attacks

**Acceptance Criteria**:
- All API endpoints MUST require authentication (except health check)
- Rate limiting MUST be enforced (100 requests/minute per user)
- Request validation MUST be enabled for all endpoints
- CORS MUST be configured with specific origins only
- API keys MUST be required for third-party integrations
- WAF rules MUST protect against common attacks (SQL injection, XSS)
- TLS 1.3 MUST be enforced for all connections

**API Gateway Configuration**:
```yaml
api_gateway_config:
  name: trustgraph-api-production
  protocol: HTTPS
  stage: prod
  
  authentication:
    default_authorizer: jwt-authorizer
    lambda_authorizer_uri: arn:aws:lambda:ap-south-1:ACCOUNT:function:jwt-validator
    authorization_caching: true
    cache_ttl: 300
  
  rate_limiting:
    burst_limit: 200
    rate_limit: 100
    quota_limit: 10000
    quota_period: DAY
  
  request_validation:
    validate_request_body: true
    validate_request_parameters: true
    validate_response: false
  
  cors_configuration:
    allow_origins:
      - https://trustgraph.gov.in
      - https://app.trustgraph.gov.in
    allow_methods: [GET, POST, PUT, DELETE, OPTIONS]
    allow_headers: [Content-Type, Authorization, X-Request-ID]
    max_age: 3600
    allow_credentials: true
  
  waf_rules:
    - name: rate-limit-rule
      priority: 1
      action: BLOCK
    - name: sql-injection-rule
      priority: 2
      action: BLOCK
    - name: xss-rule
      priority: 3
      action: BLOCK
    - name: geo-blocking-rule
      priority: 4
      action: ALLOW
      countries: [IN]  # Only allow traffic from India
```

