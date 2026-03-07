"""
TrustGraph Engine - Production API with AWS Bedrock Integration
Real working prototype for hackathon demo
"""

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import services
from src.services.bedrock_service import bedrock_service
from src.services.auth_service import auth_service
from src.services.trust_score_service import trust_score_service
from src.services.digital_wallet_service import digital_wallet_service
from src.services.milestone_contract_service import milestone_contract_service
from src.database import db
from src.security import init_security
from src.middleware import (
    SecurityHeadersMiddleware,
    AuditLogMiddleware,
    RateLimiter
)
from src.handlers.complete_auth_handler import router as auth_router
from src.handlers.trust_score_handler import router as trust_score_router
from src.handlers.wallet_handler import router as wallet_router
from src.handlers.milestone_handler import router as milestone_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="TrustGraph Engine - Digital ShramSetu",
    description="AWS Bedrock-powered platform for 490M informal workers",
    version="1.0.0"
)

# Initialize security
init_security('trustgraph-secret-key-change-in-production')

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLogMiddleware)
app.middleware("http")(RateLimiter(requests_per_minute=60))

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(trust_score_router)
app.include_router(wallet_router)
app.include_router(milestone_router)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve frontend HTML files
@app.get("/auth.html", response_class=HTMLResponse)
async def serve_auth_page():
    """Serve authentication page"""
    try:
        with open("frontend/auth.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Auth page not found")

@app.get("/index.html", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve dashboard page"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/test_ui.html", response_class=HTMLResponse)
async def serve_test_ui():
    """Serve test UI page"""
    try:
        with open("test_ui.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Test UI not found")

@app.get("/lang_demo.html", response_class=HTMLResponse)
async def serve_lang_demo():
    """Serve language demo page"""
    try:
        with open("frontend/lang_demo.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Language demo not found")

# Serve CSS files
@app.get("/styles.css")
async def serve_styles():
    return FileResponse("frontend/styles.css", media_type="text/css")

@app.get("/themes.css")
async def serve_themes():
    return FileResponse("frontend/themes.css", media_type="text/css")

@app.get("/accessibility.css")
async def serve_accessibility():
    return FileResponse("frontend/accessibility.css", media_type="text/css")

# Serve JS files
@app.get("/app.js")
async def serve_app_js():
    return FileResponse("frontend/app.js", media_type="application/javascript")

@app.get("/voice.js")
async def serve_voice_js():
    return FileResponse("frontend/voice.js", media_type="application/javascript")

@app.get("/performance.js")
async def serve_performance_js():
    return FileResponse("frontend/performance.js", media_type="application/javascript")

@app.get("/i18n.js")
async def serve_i18n_js():
    return FileResponse("frontend/i18n.js", media_type="application/javascript")

# Request models
class IntentRequest(BaseModel):
    text: str
    language: str = "hi"
    user_id: Optional[str] = None

class TrustScoreRequest(BaseModel):
    worker_id: str
    include_history: bool = False

class AuthInitRequest(BaseModel):
    aadhaar_number: str
    phone: str

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str

class VoiceCommandRequest(BaseModel):
    text: str  # In production, this would be audio_data
    language: str = "hi"
    user_id: str

# Root endpoint with beautiful UI
@app.get("/", response_class=HTMLResponse)
async def root():
    """Beautiful landing page"""
    
    html = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrustGraph - डिजिटल श्रमसेतु | 490M Workers Empowerment Platform</title>
    <script src="i18n.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        /* Language Switcher */
        .lang-switcher {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }
        
        .lang-btn {
            background: white;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 25px;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }
        
        .lang-btn:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transform: translateY(-2px);
        }
        
        .lang-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 10px;
            background: white;
            border: 2px solid #ddd;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            min-width: 200px;
            max-height: 400px;
            overflow-y: auto;
            display: none;
        }
        
        .lang-dropdown.active {
            display: block;
            animation: slideDown 0.3s ease-out;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .lang-option {
            padding: 12px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .lang-option:last-child {
            border-bottom: none;
        }
        
        .lang-option:hover {
            background: #f5f5f5;
        }
        
        .lang-option.active {
            background: #e3f2fd;
            font-weight: bold;
        }
        
        .lang-flag {
            font-size: 20px;
        }
        
        .lang-name {
            flex: 1;
        }
        
        .lang-check {
            color: #4CAF50;
            font-size: 18px;
        }
        
        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        .hero h1 {
            font-size: 3.5em;
            margin-bottom: 20px;
            animation: fadeInDown 1s ease-out;
        }
        
        .hero .tagline {
            font-size: 1.5em;
            margin-bottom: 40px;
            opacity: 0.95;
            animation: fadeInUp 1s ease-out 0.3s both;
        }
        
        .hero .stats {
            display: flex;
            gap: 40px;
            margin: 40px 0;
            flex-wrap: wrap;
            justify-content: center;
            animation: fadeInUp 1s ease-out 0.6s both;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            color: #FFD700;
        }
        
        .stat-label {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .cta-buttons {
            display: flex;
            gap: 20px;
            margin-top: 40px;
            flex-wrap: wrap;
            justify-content: center;
            animation: fadeInUp 1s ease-out 0.9s both;
        }
        
        .btn {
            padding: 18px 40px;
            font-size: 1.2em;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        
        .btn-primary {
            background: white;
            color: #667eea;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        
        .btn-secondary {
            background: transparent;
            color: white;
            border: 3px solid white;
        }
        
        .btn-secondary:hover {
            background: white;
            color: #667eea;
        }
        
        /* Animations */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero h1 {
                font-size: 2.5em;
            }
            
            .hero .tagline {
                font-size: 1.2em;
            }
            
            .stat-number {
                font-size: 2em;
            }
            
            .cta-buttons {
                flex-direction: column;
                width: 100%;
            }
            
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <!-- Language Switcher -->
    <div class="lang-switcher">
        <button class="lang-btn" onclick="toggleLangDropdown()">
            <span class="lang-flag" id="currentLangFlag">🇮🇳</span>
            <span class="lang-name" id="currentLangName">हिन्दी</span>
            <span>▼</span>
        </button>
        
        <div class="lang-dropdown" id="langDropdown"></div>
    </div>

    <!-- Hero Section -->
    <section class="hero">
        <h1>🇮🇳 TrustGraph</h1>
        <p class="tagline" data-i18n="digitalShramSetu">डिजिटल श्रमसेतु</p>
        <p class="tagline" data-i18n="empowering">Empowering 490 Million Informal Workers</p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">490M</div>
                <div class="stat-label">Workers Targeted</div>
            </div>
            <div class="stat">
                <div class="stat-number">22</div>
                <div class="stat-label">Languages Supported</div>
            </div>
            <div class="stat">
                <div class="stat-number">100%</div>
                <div class="stat-label">Secure & Private</div>
            </div>
        </div>
        
        <div class="cta-buttons">
            <a href="/auth.html" class="btn btn-primary" data-i18n="getStarted">Get Started / शुरू करें</a>
            <a href="/docs" class="btn btn-secondary">API Documentation</a>
        </div>
    </section>
    
    <script>
        function toggleLangDropdown() {
            const dropdown = document.getElementById('langDropdown');
            dropdown.classList.toggle('active');
        }
        
        function populateLanguages() {
            const dropdown = document.getElementById('langDropdown');
            const languages = getAvailableLanguages();
            const currentLang = getCurrentLanguage();
            
            dropdown.innerHTML = languages.map(lang => `
                <div class="lang-option ${lang.code === currentLang ? 'active' : ''}" 
                     onclick="changeLang('${lang.code}')">
                    <span class="lang-flag">${lang.flag}</span>
                    <span class="lang-name">${lang.name}</span>
                    ${lang.code === currentLang ? '<span class="lang-check">✓</span>' : ''}
                </div>
            `).join('');
        }
        
        function changeLang(langCode) {
            setLanguage(langCode);
            updateCurrentLangDisplay();
            populateLanguages();
            toggleLangDropdown();
        }
        
        function updateCurrentLangDisplay() {
            const currentLang = getCurrentLanguage();
            const langData = translations[currentLang];
            
            document.getElementById('currentLangFlag').textContent = langData.flag;
            document.getElementById('currentLangName').textContent = langData.name;
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const switcher = document.querySelector('.lang-switcher');
            const dropdown = document.getElementById('langDropdown');
            
            if (switcher && !switcher.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });
        
        // Initialize on load
        window.addEventListener('load', () => {
            populateLanguages();
            updateCurrentLangDisplay();
        });
    </script>
</body>
</html>
    """
    return html

@app.get("/api/health")
async def health_check():
    """Health check with Bedrock status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "operational",
            "bedrock": "connected" if bedrock_service.bedrock else "fallback",
            "auth": "operational",
            "model": bedrock_service.model_id if bedrock_service.bedrock else "rule-based"
        },
        "region": bedrock_service.region
    }

# Authentication endpoints
@app.post("/api/auth/init")
async def init_auth(request: AuthInitRequest):
    """Initialize authentication with Aadhaar and phone"""
    try:
        result = auth_service.initiate_aadhaar_auth(
            aadhaar_number=request.aadhaar_number,
            phone=request.phone
        )
        return result
    except Exception as e:
        logger.error(f"Auth init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/verify")
async def verify_auth(request: OTPVerifyRequest):
    """Verify OTP and complete authentication"""
    try:
        result = auth_service.verify_otp(
            phone=request.phone,
            otp=request.otp
        )
        return result
    except Exception as e:
        logger.error(f"Auth verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/user/{user_id}")
async def get_user(user_id: str):
    """Get user profile"""
    user = auth_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/intent/classify")
async def classify_intent(request: IntentRequest):
    """
    Classify user intent using AWS Bedrock Claude 3 Haiku
    
    This is the REAL implementation using AWS Bedrock GenAI
    """
    try:
        logger.info(f"Classifying intent for text: {request.text[:50]}...")
        
        # Call Bedrock service
        result = await bedrock_service.classify_intent(
            text=request.text,
            language=request.language
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice command with intent classification"""
    try:
        # Classify intent
        intent_result = await bedrock_service.classify_intent(
            text=request.text,
            language=request.language
        )
        
        # Generate response based on intent
        responses = {
            "CHECK_TRUST_SCORE": "आपका ट्रस्ट स्कोर 720 है। यह एक अच्छा स्कोर है।",
            "ADD_WORK_RECORD": "आपका काम रिकॉर्ड जोड़ा जा रहा है। कृपया फोटो अपलोड करें।",
            "REQUEST_PAYMENT": "आपका पेमेंट रिक्वेस्ट भेजा जा रहा है। 24 घंटे में पैसे मिलेंगे।",
            "VERIFY_CREDENTIAL": "आपके पास 15 वेरिफाइड सर्टिफिकेट हैं।",
            "RAISE_DISPUTE": "आपकी समस्या दर्ज की गई है। हम 48 घंटे में जवाब देंगे।",
            "GET_HELP": "मैं आपकी मदद के लिए यहाँ हूँ। आप क्या जानना चाहते हैं?"
        }
        
        response_text = responses.get(
            intent_result['intent'],
            "मुझे समझ नहीं आया। कृपया दोबारा बोलें।"
        )
        
        return {
            "success": True,
            "transcription": request.text,
            "intent": intent_result,
            "response": {
                "text": response_text,
                "language": request.language
            },
            "user_id": request.user_id
        }
        
    except Exception as e:
        logger.error(f"Voice command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trust/calculate")
async def calculate_trust_score(request: TrustScoreRequest):
    """Calculate trust score (mock for now, GNN implementation pending)"""
    
    # Mock trust score calculation
    import random
    
    score = random.randint(650, 850)
    
    return {
        "worker_id": request.worker_id,
        "trust_score": score,
        "confidence": 0.87,
        "factors": {
            "work_history": 0.85,
            "payment_reliability": 0.90,
            "skill_verification": 0.82,
            "social_proof": 0.78
        },
        "risk_level": "low" if score > 750 else "medium",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/demo/worker/{worker_id}")
async def get_worker_demo(worker_id: str):
    """Get demo worker profile"""
    return {
        "worker_id": worker_id,
        "name": "राम कुमार (Ram Kumar)",
        "phone": "+91-9876543210",
        "location": "Noida, Uttar Pradesh",
        "preferred_language": "hi",
        "skills": ["construction", "painting", "electrical"],
        "trust_score": 720,
        "total_work_hours": 1200,
        "credentials_count": 15,
        "average_rating": 4.3,
        "verification_status": "verified"
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Starting TrustGraph Engine with AWS Bedrock")
    print("=" * 60)
    print(f"Bedrock Status: {'Connected' if bedrock_service.bedrock else 'Fallback Mode'}")
    print(f"Model: {bedrock_service.model_id if bedrock_service.bedrock else 'Rule-based'}")
    print(f"Region: {bedrock_service.region}")
    print("=" * 60)
    print("Open: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
