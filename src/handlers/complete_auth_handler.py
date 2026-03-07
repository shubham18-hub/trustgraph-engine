"""
Complete Authentication Handler
Handles signup, login, OTP verification, profile management, and Aadhaar verification
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import logging

from src.services.auth_service import auth_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Request models
class SignupRequest(BaseModel):
    phone: str
    aadhaar_number: str
    name: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    preferred_language: Optional[str] = "hi"
    
    @validator('phone')
    def validate_phone(cls, v):
        phone = v.replace('+91', '').replace(' ', '').replace('-', '')
        if len(phone) != 10 or not phone.isdigit():
            raise ValueError('Phone must be 10 digits')
        return phone
    
    @validator('aadhaar_number')
    def validate_aadhaar(cls, v):
        aadhaar = v.replace(' ', '').replace('-', '')
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            raise ValueError('Aadhaar must be 12 digits')
        return aadhaar

class VerifySignupOTPRequest(BaseModel):
    phone: str
    otp: str
    signup_data: dict

class LoginRequest(BaseModel):
    phone: str

class VerifyLoginOTPRequest(BaseModel):
    phone: str
    otp: str

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    preferred_language: Optional[str] = None

class VerifyAadhaarRequest(BaseModel):
    otp: str

# Endpoints
@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Complete user signup
    
    Steps:
    1. Validate all input data
    2. Check if user already exists
    3. Generate and send OTP
    4. Return transaction details
    """
    try:
        result = auth_service.signup(request.dict())
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": result['message'],
            "phone": result['phone'],
            "expires_in": result['expires_in'],
            "next_step": result['next_step'],
            "otp_demo": result.get('otp_demo'),  # For testing only
            "signup_data": result.get('signup_data')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed")

@router.post("/signup/verify")
async def verify_signup(request: VerifySignupOTPRequest):
    """
    Verify OTP and complete signup
    
    Returns JWT token and user profile
    """
    try:
        result = auth_service.verify_signup_otp(
            request.phone,
            request.otp,
            request.signup_data
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": result['message'],
            "token": result['token'],
            "session_id": result['session_id'],
            "user_profile": result['user_profile']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.post("/login")
async def login(request: LoginRequest):
    """
    Initiate login with phone number
    
    Steps:
    1. Check if user exists
    2. Generate and send OTP
    3. Return transaction details
    """
    try:
        result = auth_service.login(request.phone)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": result['message'],
            "phone": result['phone'],
            "expires_in": result['expires_in'],
            "next_step": result['next_step'],
            "otp_demo": result.get('otp_demo')  # For testing only
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/login/verify")
async def verify_login(request: VerifyLoginOTPRequest):
    """
    Verify OTP and complete login
    
    Returns JWT token and user profile
    """
    try:
        result = auth_service.verify_login_otp(request.phone, request.otp)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": result['message'],
            "token": result['token'],
            "session_id": result['session_id'],
            "user_profile": result['user_profile']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.get("/profile/{user_id}")
async def get_profile(user_id: str, authorization: Optional[str] = Header(None)):
    """Get user profile"""
    try:
        # In production: Verify JWT token from authorization header
        user = auth_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "user_profile": {
                "user_id": user['user_id'],
                "name": user.get('name'),
                "phone": user['phone'],
                "email": user.get('email'),
                "date_of_birth": user.get('date_of_birth'),
                "gender": user.get('gender'),
                "address": user.get('address'),
                "city": user.get('city'),
                "state": user.get('state'),
                "pincode": user.get('pincode'),
                "role": user['role'],
                "preferred_language": user.get('preferred_language'),
                "kyc_status": user.get('kyc_status'),
                "aadhaar_verified": bool(user.get('aadhaar_verified')),
                "account_status": user.get('account_status'),
                "created_at": user.get('created_at'),
                "last_login": user.get('last_login')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@router.put("/profile/{user_id}")
async def update_profile(
    user_id: str,
    request: UpdateProfileRequest,
    authorization: Optional[str] = Header(None)
):
    """Update user profile"""
    try:
        # In production: Verify JWT token and ensure user_id matches
        result = auth_service.update_profile(user_id, request.dict(exclude_none=True))
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": result['message'],
            "user_profile": result['user_profile']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

@router.post("/aadhaar/verify/{user_id}")
async def verify_aadhaar(
    user_id: str,
    request: VerifyAadhaarRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Verify Aadhaar with OTP
    
    In production: Integrate with UIDAI API
    """
    try:
        # In production: Verify JWT token
        result = auth_service.verify_aadhaar_otp(user_id, request.otp)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": result['message'],
            "kyc_status": result['kyc_status']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Aadhaar verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.post("/logout")
async def logout(session_id: str, authorization: Optional[str] = Header(None)):
    """Logout user"""
    try:
        # In production: Verify JWT token and invalidate session
        result = auth_service.logout(session_id)
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")
