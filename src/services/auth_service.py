"""
Authentication Service for TrustGraph Engine
Implements Aadhaar-based authentication with voice biometric secondary factor
"""
import boto3
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.utils.crypto import generate_keypair, sign_data
from src.models.user import User

logger = get_logger(__name__)

class AuthService:
    """Handles authentication operations for Digital ShramSetu platform"""
    
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.dynamodb = boto3.resource('dynamodb')
        self.users_table = self.dynamodb.Table('trustgraph-users')
        self.sessions_table = self.dynamodb.Table('trustgraph-sessions')
        
    def initiate_aadhaar_auth(self, aadhaar_number: str) -> Dict[str, Any]:
        """
        Initiate Aadhaar-based authentication via UIDAI API
        
        Args:
            aadhaar_number: 12-digit Aadhaar number
            
        Returns:
            Dict containing transaction_id for OTP verification
        """
        try:
            # Validate Aadhaar number format
            if not self._validate_aadhaar(aadhaar_number):
                raise ValueError("Invalid Aadhaar number format")
            
            # Hash Aadhaar for privacy (store hash, not actual number)
            aadhaar_hash = hashlib.sha256(aadhaar_number.encode()).hexdigest()
            
            # Generate transaction ID for this auth session
            transaction_id = self._generate_transaction_id()
            
            # In production, integrate with UIDAI Authentication API
            # For now, simulate OTP generation
            otp_sent = self._send_aadhaar_otp(aadhaar_number, transaction_id)
            
            if otp_sent:
                # Store transaction details temporarily
                self._store_auth_transaction(transaction_id, aadhaar_hash)
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'message': 'OTP sent to registered mobile number',
                    'expires_in': 300  # 5 minutes
                }
            else:
                raise Exception("Failed to send OTP")
                
        except Exception as e:
            logger.error(f"Aadhaar auth initiation failed: {str(e)}")
            return {
                'success': False,
                'error': 'Authentication initiation failed'
            }
    
    def verify_otp(self, transaction_id: str, otp: str) -> Dict[str, Any]:
        """
        Verify OTP and create authenticated session
        
        Args:
            transaction_id: Transaction ID from initiate_aadhaar_auth
            otp: 6-digit OTP received via SMS
            
        Returns:
            Dict containing JWT token and user profile
        """
        try:
            # Retrieve transaction details
            transaction = self._get_auth_transaction(transaction_id)
            if not transaction:
                return {'success': False, 'error': 'Invalid transaction ID'}
            
            # Verify OTP (in production, verify with UIDAI)
            if not self._verify_aadhaar_otp(transaction_id, otp):
                return {'success': False, 'error': 'Invalid OTP'}
            
            # Get or create user profile
            user = self._get_or_create_user(transaction['aadhaar_hash'])
            
            # Generate JWT token
            token = self._generate_jwt_token(user)
            
            # Create session record
            session_id = self._create_user_session(user['user_id'], token)
            
            # Clean up transaction record
            self._cleanup_auth_transaction(transaction_id)
            
            return {
                'success': True,
                'token': token,
                'user_profile': {
                    'user_id': user['user_id'],
                    'role': user['role'],
                    'created_at': user['created_at'],
                    'verified': user['verified']
                },
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            return {'success': False, 'error': 'OTP verification failed'}
    
    def verify_voice_biometric(self, user_id: str, voice_sample: str) -> Dict[str, Any]:
        """
        Verify voice biometric as secondary authentication factor
        
        Args:
            user_id: User identifier
            voice_sample: Base64 encoded voice sample
            
        Returns:
            Dict containing verification result
        """
        try:
            # Get user's stored voice print
            user = self._get_user_by_id(user_id)
            if not user or not user.get('voice_print'):
                return {'success': False, 'error': 'Voice biometric not enrolled'}
            
            # Compare voice samples using AWS services
            # In production, use Amazon Connect Voice ID or similar
            match_score = self._compare_voice_samples(user['voice_print'], voice_sample)
            
            # Threshold for voice match (configurable)
            voice_threshold = 0.85
            
            if match_score >= voice_threshold:
                # Update session with voice verification
                self._update_session_voice_verified(user_id)
                
                return {
                    'success': True,
                    'match_score': match_score,
                    'verified': True
                }
            else:
                return {
                    'success': False,
                    'match_score': match_score,
                    'error': 'Voice biometric verification failed'
                }
                
        except Exception as e:
            logger.error(f"Voice biometric verification failed: {str(e)}")
            return {'success': False, 'error': 'Voice verification failed'}
    
    def _validate_aadhaar(self, aadhaar_number: str) -> bool:
        """Validate Aadhaar number format and checksum"""
        if len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            return False
        
        # Implement Verhoeff algorithm for Aadhaar checksum validation
        # Simplified validation for demo
        return True
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID for auth se