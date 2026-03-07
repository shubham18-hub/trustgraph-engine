# TrustGraph Engine API Documentation

## Base URL
```
Production: https://api.trustgraph.gov.in
Development: http://localhost:8000/api
```

## Authentication
All authenticated endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-26T10:00:00Z",
  "services": {
    "api": "operational",
    "bedrock": "connected",
    "auth": "operational"
  }
}
```

### Authentication

#### Initialize Authentication
```http
POST /auth/init
```

**Request:**
```json
{
  "aadhaar_number": "123456789012",
  "phone": "9876543210"
}
```

**Response:**
```json
{
  "success": true,
  "phone": "+919876543210",
  "message": "OTP sent successfully",
  "otp_demo": "123456"
}
```

#### Verify OTP
```http
POST /auth/verify
```

**Request:**
```json
{
  "phone": "+919876543210",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_profile": {
    "user_id": "user_123",
    "phone": "+919876543210",
    "role": "worker"
  }
}
```

### Voice Interface

#### Classify Intent
```http
POST /intent/classify
```

**Request:**
```json
{
  "text": "मेरा ट्रस्ट स्कोर क्या है?",
  "language": "hi"
}
```

**Response:**
```json
{
  "intent": "CHECK_TRUST_SCORE",
  "confidence": 0.95,
  "language": "hi",
  "source": "aws-bedrock",
  "latency_ms": 150
}
```

**Supported Intents:**
- `CHECK_TRUST_SCORE` - Check trust score
- `ADD_WORK_RECORD` - Add work completion
- `REQUEST_PAYMENT` - Request payment
- `VERIFY_CREDENTIAL` - Verify credentials
- `RAISE_DISPUTE` - Raise dispute
- `GET_HELP` - Get help

#### Process Voice Command
```http
POST /voice/command
```

**Request:**
```json
{
  "text": "काम पूरा हो गया",
  "language": "hi",
  "user_id": "worker_123"
}
```

**Response:**
```json
{
  "success": true,
  "transcription": "काम पूरा हो गया",
  "intent": {
    "intent": "ADD_WORK_RECORD",
    "confidence": 0.92
  },
  "response": {
    "text": "आपका काम रिकॉर्ड जोड़ा जा रहा है।",
    "language": "hi"
  }
}
```

### Trust Scoring

#### Calculate Trust Score
```http
POST /trust/calculate
```

**Request:**
```json
{
  "worker_id": "worker_123",
  "include_history": false
}
```

**Response:**
```json
{
  "worker_id": "worker_123",
  "trust_score": 720,
  "confidence": 0.87,
  "factors": {
    "work_history": 0.85,
    "payment_reliability": 0.90,
    "skill_verification": 0.82,
    "social_proof": 0.78
  },
  "risk_level": "low",
  "timestamp": "2024-01-26T10:00:00Z"
}
```

### Demo Endpoints

#### Get Worker Profile
```http
GET /demo/worker/{worker_id}
```

**Response:**
```json
{
  "worker_id": "worker_123",
  "name": "राम कुमार (Ram Kumar)",
  "phone": "+91-9876543210",
  "location": "Noida, Uttar Pradesh",
  "preferred_language": "hi",
  "skills": ["construction", "painting", "electrical"],
  "trust_score": 720,
  "total_work_hours": 1200,
  "credentials_count": 15,
  "average_rating": 4.3
}
```

## Error Responses

All errors follow this format:
```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

**Common Error Codes:**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

## Rate Limiting
- 60 requests per minute per IP
- 1000 requests per hour per user

## Supported Languages
- Hindi (hi)
- English (en)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)
- Punjabi (pa)
