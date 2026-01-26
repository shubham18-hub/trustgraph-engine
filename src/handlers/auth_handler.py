"""
Authentication Handler for TrustGraph Engine
Handles Aadhaar-based OTP and voice biometric authentication
"""
import json
import boto3
from typing import Dict, Any
from src.services.auth_service import AuthService
from src.utils.response import create_response
from src.utils.logger import get_logger

logger = get_logger(__name__)
auth_service = AuthService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for authentication operations
    
    Supported operations:
    - POST /auth/login - Initiate Aadhaar OTP
    - POST /auth/verify-otp - Verify OTP and create session
    - POST /auth/voice-verify - Voice biometric verification
    """
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')
        body = json.loads(event.get('body', '{}'))
        
        logger.info(f"Auth request: {http_method} {path}")
        
        if path == '/auth/login' and http_method == 'POST':
            return handle_login(body)
        elif path == '/auth/verify-otp' and http_method == 'POST':
            return handle_verify_otp(body)
        elif path == '/auth/voice-verify' and http_method == 'POST':
            return handle_voice_verify(body)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def handle_login(body: Dict[str, Any]) -> Dict[str, Any]:
    """Initiate Aadhaar-based login"""
    aadhaar_number = body.get('aadhaar_number')
    
    if not aadhaar_number:
        return create_response(400, {'error': 'Aadhaar number required'})
    
    result = auth_service.initiate_aadhaar_auth(aadhaar_number)
    return create_response(200, result)

def handle_verify_otp(body: Dict[str, Any]) -> Dict[str, Any]:
    """Verify OTP and create authenticated session"""
    transaction_id = body.get('transaction_id')
    otp = body.get('otp')
    
    if not transaction_id or not otp:
        return create_response(400, {'error': 'Transaction ID and OTP required'})
    
    result = auth_service.verify_otp(transaction_id, otp)
    return create_response(200, result)

def handle_voice_verify(body: Dict[str, Any]) -> Dict[str, Any]:
    """Voice biometric verification as secondary factor"""
    user_id = body.get('user_id')
    voice_sample = body.get('voice_sample')
    
    if not user_id or not voice_sample:
        return create_response(400, {'error': 'User ID and voice sample required'})
    
    result = auth_service.verify_voice_biometric(user_id, voice_sample)
    return create_response(200, result)