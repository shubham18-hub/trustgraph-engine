"""Unit tests for authentication service"""

import pytest
from src.services.auth_service import auth_service
from src.security import init_security

@pytest.fixture
def setup_security():
    """Initialize security manager for tests"""
    init_security('test-secret-key-12345')

def test_initiate_aadhaar_auth(setup_security):
    """Test Aadhaar authentication initiation"""
    result = auth_service.initiate_aadhaar_auth(
        aadhaar_number='123456789012',
        phone='9876543210'
    )
    
    assert result['success'] is True
    assert 'otp_demo' in result
    assert len(result['otp_demo']) == 6

def test_verify_otp_success(setup_security):
    """Test successful OTP verification"""
    # First initiate auth
    init_result = auth_service.initiate_aadhaar_auth(
        aadhaar_number='123456789012',
        phone='9876543210'
    )
    
    otp = init_result['otp_demo']
    
    # Verify OTP
    result = auth_service.verify_otp(
        phone='+919876543210',
        otp=otp
    )
    
    assert result['success'] is True
    assert 'token' in result
    assert 'user_profile' in result

def test_verify_otp_failure(setup_security):
    """Test failed OTP verification"""
    result = auth_service.verify_otp(
        phone='+919876543210',
        otp='000000'
    )
    
    assert result['success'] is False
    assert 'error' in result

def test_jwt_token_generation(setup_security):
    """Test JWT token generation and verification"""
    token = auth_service.create_jwt_token('user_123', 'worker')
    
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token
    payload = auth_service.verify_jwt_token(token)
    assert payload['user_id'] == 'user_123'
    assert payload['role'] == 'worker'

def test_rate_limiting(setup_security):
    """Test OTP rate limiting"""
    phone = '9876543210'
    
    # First 3 attempts should succeed
    for i in range(3):
        result = auth_service.initiate_aadhaar_auth(
            aadhaar_number='123456789012',
            phone=phone
        )
        assert result['success'] is True
    
    # 4th attempt should fail
    result = auth_service.initiate_aadhaar_auth(
        aadhaar_number='123456789012',
        phone=phone
    )
    assert result['success'] is False
    assert 'rate limit' in result.get('error', '').lower()

def test_aadhaar_hashing(setup_security):
    """Test Aadhaar number hashing"""
    aadhaar = '123456789012'
    hashed = auth_service.hash_aadhaar(aadhaar)
    
    assert hashed != aadhaar
    assert len(hashed) > 0
    
    # Same input should produce same hash
    hashed2 = auth_service.hash_aadhaar(aadhaar)
    assert hashed == hashed2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
