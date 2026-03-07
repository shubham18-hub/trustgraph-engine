"""
TrustGraph Engine - FastAPI Application
Main entry point for local development and testing
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
import base64
from datetime import datetime
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize FastAPI app
app = FastAPI(
    title="TrustGraph Engine - Digital ShramSetu",
    description="Voice-first platform empowering 490M informal workers in India",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    services: Dict[str, str]

class VoiceTranscribeRequest(BaseModel):
    audio_data: str  # base64 encoded
    source_language: str = "hi"
    format: str = "wav"

class VoiceCommandRequest(BaseModel):
    audio_data: str  # base64 encoded
    user_id: str
    session_context: Optional[Dict[str, Any]] = {}

class TrustScoreRequest(BaseModel):
    worker_id: str
    work_history: Optional[List[Dict]] = []
    skills: Optional[List[str]] = []

class CredentialRequest(BaseModel):
    worker_id: str
    work_type: str
    employer_id: str
    duration_hours: int
    skills_demonstrated: List[str]

# Mock services for development
class MockVoiceService:
    async def process_voice_command(self, audio_data: bytes, user_id: str, context: Dict = None):
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        return {
            "transcribed_text": "मुझे काम का प्रमाणपत्र चाहिए",
            "detected_language": "hi",
            "intent": "request_certificate",
            "entities": {"work_type": "construction"},
            "confidence": 0.92,
            "response_text": "आपका काम प्रमाणपत्र तैयार हो रहा है। कृपया अपना आधार नंबर बताएं।",
            "response_audio_url": "https://example.com/audio/response.wav",
            "session_id": f"session_{user_id}_{int(datetime.now().timestamp())}",
            "processing_time_ms": 500,
            "fallback_used": False
        }

class MockTrustScoreService:
    async def calculate_trust_score(self, worker_data: Dict):
        await asyncio.sleep(0.2)
        
        # Mock calculation
        base_score = 500
        work_history_bonus = len(worker_data.get("work_history", [])) * 10
        skills_bonus = len(worker_data.get("skills", [])) * 5
        
        score = min(850, max(300, base_score + work_history_bonus + skills_bonus))
        
        return {
            "worker_id": worker_data["worker_id"],
            "trust_score": score,
            "confidence": 0.87,
            "factors": {
                "work_history_count": len(worker_data.get("work_history", [])),
                "skills_count": len(worker_data.get("skills", [])),
                "consistency_score": 0.85,
                "social_proof_score": 0.78
            },
            "risk_assessment": "low" if score > 650 else "medium" if score > 500 else "high",
            "timestamp": datetime.now().isoformat()
        }

class MockBlockchainService:
    async def mint_credential(self, credential_data: Dict):
        await asyncio.sleep(0.3)
        
        credential_id = f"cred_{credential_data['worker_id']}_{int(datetime.now().timestamp())}"
        
        return {
            "credential_id": credential_id,
            "worker_id": credential_data["worker_id"],
            "work_type": credential_data["work_type"],
            "employer_id": credential_data["employer_id"],
            "duration_hours": credential_data["duration_hours"],
            "skills_demonstrated": credential_data["skills_demonstrated"],
            "issued_at": datetime.now().isoformat(),
            "signature": f"mock_signature_{credential_id}",
            "blockchain_hash": f"0x{credential_id}abc123",
            "verification_url": f"https://trustgraph.gov.in/verify/{credential_id}"
        }

# Initialize mock services
voice_service = MockVoiceService()
trust_service = MockTrustScoreService()
blockchain_service = MockBlockchainService()

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify all services are running"""
    return HealthResponse(
        status="healthy",
        message="TrustGraph Engine is running successfully",
        timestamp=datetime.now().isoformat(),
        services={
            "voice_processing": "operational",
            "trust_scoring": "operational", 
            "blockchain": "operational",
            "authentication": "operational"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "TrustGraph Engine - Digital ShramSetu API",
        "description": "Empowering 490 million informal workers in India",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "voice_processing": "/voice/",
            "trust_scoring": "/trust/",
            "credentials": "/credentials/",
            "authentication": "/auth/"
        }
    }

# Voice processing endpoints
@app.post("/voice/transcribe")
async def transcribe_audio(request: VoiceTranscribeRequest):
    """Transcribe audio to text using Bhashini API with AWS fallback"""
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Validate audio size (max 10MB)
        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")
        
        # Mock transcription
        await asyncio.sleep(0.5)  # Simulate processing
        
        return {
            "transcribed_text": "मुझे काम का प्रमाणपत्र चाहिए",
            "confidence_score": 0.92,
            "detected_language": request.source_language,
            "processing_info": {
                "service_used": "bhashini",
                "fallback_used": False,
                "processing_time_ms": 500
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/voice/command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process complete voice command with intent recognition"""
    try:
        # Decode audio
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Process voice command
        result = await voice_service.process_voice_command(
            audio_bytes, 
            request.user_id, 
            request.session_context
        )
        
        return {
            "status": "success",
            "data": result,
            "next_steps": [
                "Upload photo evidence if work completed",
                "Wait for employer confirmation",
                "Check payment status in 24 hours"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

# Trust scoring endpoints
@app.post("/trust/calculate")
async def calculate_trust_score(request: TrustScoreRequest):
    """Calculate trust score using Graph Neural Network model"""
    try:
        worker_data = {
            "worker_id": request.worker_id,
            "work_history": request.work_history,
            "skills": request.skills
        }
        
        result = await trust_service.calculate_trust_score(worker_data)
        
        return {
            "status": "success",
            "data": result,
            "recommendations": [
                "Complete more verified work to improve score",
                "Get skill endorsements from employers",
                "Maintain consistent payment history"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trust score calculation failed: {str(e)}")

@app.get("/trust/{worker_id}")
async def get_trust_score(worker_id: str):
    """Get existing trust score for a worker"""
    try:
        # Mock data retrieval
        await asyncio.sleep(0.1)
        
        return {
            "worker_id": worker_id,
            "current_trust_score": 720,
            "score_history": [
                {"date": "2024-01-15", "score": 680},
                {"date": "2024-01-20", "score": 700},
                {"date": "2024-01-25", "score": 720}
            ],
            "factors": {
                "work_consistency": 0.85,
                "skill_verification": 0.78,
                "employer_ratings": 0.82,
                "payment_history": 0.90
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trust score: {str(e)}")

# Credential management endpoints
@app.post("/credentials/mint")
async def mint_credential(request: CredentialRequest):
    """Mint a new W3C Verifiable Credential on blockchain"""
    try:
        credential_data = {
            "worker_id": request.worker_id,
            "work_type": request.work_type,
            "employer_id": request.employer_id,
            "duration_hours": request.duration_hours,
            "skills_demonstrated": request.skills_demonstrated
        }
        
        result = await blockchain_service.mint_credential(credential_data)
        
        return {
            "status": "success",
            "data": result,
            "verification_steps": [
                "Credential minted on blockchain",
                "Digital signature applied",
                "Available for verification by banks/employers"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credential minting failed: {str(e)}")

@app.get("/credentials/{worker_id}")
async def get_worker_credentials(worker_id: str):
    """Get all credentials for a worker"""
    try:
        # Mock credential retrieval
        await asyncio.sleep(0.2)
        
        return {
            "worker_id": worker_id,
            "credentials": [
                {
                    "credential_id": "cred_123",
                    "work_type": "construction",
                    "employer": "ABC Construction",
                    "duration_hours": 160,
                    "skills": ["masonry", "painting"],
                    "issued_date": "2024-01-15",
                    "verified": True
                },
                {
                    "credential_id": "cred_124", 
                    "work_type": "delivery",
                    "employer": "XYZ Logistics",
                    "duration_hours": 80,
                    "skills": ["driving", "customer_service"],
                    "issued_date": "2024-01-20",
                    "verified": True
                }
            ],
            "total_credentials": 2,
            "total_work_hours": 240,
            "unique_skills": ["masonry", "painting", "driving", "customer_service"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve credentials: {str(e)}")

# Authentication endpoints
@app.post("/auth/verify")
async def verify_user(user_data: Dict[str, Any]):
    """Verify user identity using Aadhaar + voice biometric"""
    try:
        # Mock authentication
        await asyncio.sleep(0.3)
        
        return {
            "verified": True,
            "user_id": user_data.get("user_id", "worker_123"),
            "verification_methods": ["aadhaar_otp", "voice_biometric"],
            "confidence_score": 0.94,
            "session_token": f"token_{int(datetime.now().timestamp())}",
            "expires_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

# Demo endpoints for testing
@app.get("/demo/worker/{worker_id}")
async def get_demo_worker_profile(worker_id: str):
    """Get demo worker profile for testing"""
    return {
        "worker_id": worker_id,
        "name": "राम कुमार",
        "phone": "+91-9876543210",
        "location": "Noida, Uttar Pradesh",
        "preferred_language": "hi",
        "skills": ["construction", "painting", "electrical"],
        "trust_score": 720,
        "total_work_hours": 1200,
        "credentials_count": 15,
        "average_rating": 4.3,
        "last_work_date": "2024-01-25",
        "payment_status": "up_to_date",
        "verification_status": "verified"
    }

@app.get("/demo/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "supported_languages": {
            "hi": "हिन्दी (Hindi)",
            "bn": "বাংলা (Bengali)", 
            "te": "తెలుగు (Telugu)",
            "mr": "मराठी (Marathi)",
            "ta": "தமிழ் (Tamil)",
            "gu": "ગુજરાતી (Gujarati)",
            "kn": "ಕನ್ನಡ (Kannada)",
            "ml": "മലയാളം (Malayalam)",
            "or": "ଓଡ଼ିଆ (Odia)",
            "pa": "ਪੰਜਾਬੀ (Punjabi)",
            "as": "অসমীয়া (Assamese)",
            "ur": "اردو (Urdu)",
            "en": "English"
        },
        "total_languages": 13,
        "voice_support": "full",
        "text_support": "full"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)