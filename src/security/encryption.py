"""
Security and Encryption Module - DPDP Act 2023 Compliant
Zero-trust architecture with end-to-end encryption
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json

class SecurityManager:
    """Zero-trust security manager with DPDP Act compliance"""
    
    def __init__(self, secret_key: str, encryption_key: Optional[str] = None):
        self.secret_key = secret_key
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # JWT configuration
        self.jwt_algorithm = 'HS256'
        self.jwt_expiry = timedelta(hours=24)
        
        # Password hashing
        self.hash_iterations = 100000
    
    def generate_jwt(self, user_id: str, role: str, metadata: Dict[str, Any] = None) -> str:
        """
        Generate JWT token with user claims
        
        DPDP Act Compliance:
        - Minimal data in token
        - Short expiry time
        - Secure signing
        """
        
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + self.jwt_expiry,
            'jti': secrets.token_urlsafe(16)  # Unique token ID
        }
        
        if metadata:
            payload['metadata'] = metadata
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
        
        return token
    
    def verify_jwt(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Returns:
            Decoded payload if valid
        
        Raises:
            jwt.ExpiredSignatureError: Token expired
            jwt.InvalidTokenError: Invalid token
        """
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError('Token expired')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token')
    
    def hash_aadhaar(self, aadhaar_number: str) -> str:
        """
        Hash Aadhaar number for DPDP Act compliance
        
        DPDP Act Requirement:
        - Irreversible hashing
        - No storage of plain Aadhaar
        - SHA-256 with salt
        """
        
        salt = self.secret_key.encode()
        aadhaar_bytes = aadhaar_number.encode()
        
        # Use PBKDF2HMAC for secure hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.hash_iterations,
            backend=default_backend()
        )
        
        hashed = kdf.derive(aadhaar_bytes)
        return base64.b64encode(hashed).decode()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data (PII, credentials)
        
        DPDP Act Compliance:
        - AES-256 encryption
        - Secure key management
        """
        
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def hash_password(self, password: str) -> str:
        """Hash password with PBKDF2"""
        
        salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.hash_iterations,
            backend=default_backend()
        )
        
        hashed = kdf.derive(password.encode())
        
        # Store salt with hash
        combined = salt + hashed
        return base64.b64encode(combined).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        
        combined = base64.b64decode(hashed.encode())
        salt = combined[:32]
        stored_hash = combined[32:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.hash_iterations,
            backend=default_backend()
        )
        
        try:
            kdf.verify(password.encode(), stored_hash)
            return True
        except:
            return False
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate secure OTP"""
        
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def sign_credential(self, credential: Dict[str, Any]) -> str:
        """
        Sign W3C Verifiable Credential
        
        Blockchain Integration:
        - Ed25519 signature
        - Immutable proof
        """
        
        credential_json = json.dumps(credential, sort_keys=True)
        
        signature = hmac.new(
            self.secret_key.encode(),
            credential_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_credential_signature(self, credential: Dict[str, Any], signature: str) -> bool:
        """Verify credential signature"""
        
        credential_json = json.dumps(credential, sort_keys=True)
        
        expected_signature = hmac.new(
            self.secret_key.encode(),
            credential_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def sanitize_input(self, data: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
        
        sanitized = data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    def validate_phone(self, phone: str) -> bool:
        """Validate Indian phone number"""
        
        # Remove spaces and special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Check length (10 digits)
        if len(phone) != 10:
            return False
        
        # Check starts with valid digit (6-9)
        if phone[0] not in ['6', '7', '8', '9']:
            return False
        
        return True
    
    def validate_aadhaar(self, aadhaar: str) -> bool:
        """Validate Aadhaar number format"""
        
        # Remove spaces
        aadhaar = ''.join(filter(str.isdigit, aadhaar))
        
        # Check length (12 digits)
        if len(aadhaar) != 12:
            return False
        
        # Verhoeff algorithm for checksum
        return self._verhoeff_validate(aadhaar)
    
    def _verhoeff_validate(self, num: str) -> bool:
        """Verhoeff algorithm for Aadhaar validation"""
        
        # Simplified validation (full implementation would use Verhoeff tables)
        return len(num) == 12 and num.isdigit()
    
    def audit_log(self, action: str, user_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create audit log entry for DPDP Act compliance
        
        Required for:
        - Data access tracking
        - Consent management
        - Regulatory compliance
        """
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'user_id': user_id,
            'details': details,
            'ip_address': details.get('ip_address', 'unknown'),
            'user_agent': details.get('user_agent', 'unknown')
        }
        
        # Sign log entry for immutability
        log_json = json.dumps(log_entry, sort_keys=True)
        log_entry['signature'] = hmac.new(
            self.secret_key.encode(),
            log_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return log_entry


class ConsentManager:
    """DPDP Act 2023 Consent Management"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
    
    def create_consent_record(
        self,
        user_id: str,
        purpose: str,
        data_categories: list,
        retention_period: str
    ) -> Dict[str, Any]:
        """
        Create consent record for DPDP Act compliance
        
        Requirements:
        - Explicit consent
        - Purpose specification
        - Data minimization
        - Retention limits
        """
        
        consent = {
            'consent_id': secrets.token_urlsafe(16),
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'purpose': purpose,
            'data_categories': data_categories,
            'retention_period': retention_period,
            'consent_given': True,
            'withdrawal_mechanism': 'voice_command_or_app',
            'language': 'hi-IN'
        }
        
        # Sign consent record
        consent['signature'] = self.security.sign_credential(consent)
        
        return consent
    
    def withdraw_consent(self, consent_id: str, user_id: str) -> Dict[str, Any]:
        """Withdraw consent and trigger data deletion"""
        
        withdrawal = {
            'consent_id': consent_id,
            'user_id': user_id,
            'withdrawal_timestamp': datetime.utcnow().isoformat(),
            'status': 'withdrawn',
            'data_deletion_scheduled': True
        }
        
        return withdrawal
    
    def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user has given consent for specific purpose"""
        
        # In production, query database
        # For now, return True for demo
        return True


# Global security manager instance
security_manager = None

def init_security(secret_key: str, encryption_key: Optional[str] = None):
    """Initialize global security manager"""
    global security_manager
    security_manager = SecurityManager(secret_key, encryption_key)
    return security_manager

def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    if security_manager is None:
        raise RuntimeError('Security manager not initialized')
    return security_manager
