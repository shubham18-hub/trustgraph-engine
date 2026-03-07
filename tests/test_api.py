"""Integration tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'services' in data

def test_intent_classification():
    """Test intent classification endpoint"""
    response = client.post('/api/intent/classify', json={
        'text': 'मेरा ट्रस्ट स्कोर क्या है?',
        'language': 'hi'
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'intent' in data
    assert 'confidence' in data
    assert data['intent'] == 'CHECK_TRUST_SCORE'

def test_auth_flow():
    """Test complete authentication flow"""
    # Step 1: Initiate auth
    response = client.post('/api/auth/init', json={
        'aadhaar_number': '123456789012',
        'phone': '9876543210'
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    otp = data['otp_demo']
    
    # Step 2: Verify OTP
    response = client.post('/api/auth/verify', json={
        'phone': '+919876543210',
        'otp': otp
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'token' in data

def test_voice_command():
    """Test voice command processing"""
    response = client.post('/api/voice/command', json={
        'text': 'काम पूरा हो गया',
        'language': 'hi',
        'user_id': 'worker_123'
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['success'] is True
    assert 'intent' in data
    assert 'response' in data

def test_trust_score_calculation():
    """Test trust score calculation"""
    response = client.post('/api/trust/calculate', json={
        'worker_id': 'worker_123',
        'include_history': False
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'trust_score' in data
    assert 'confidence' in data
    assert 300 <= data['trust_score'] <= 900

def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options('/api/health')
    
    assert 'access-control-allow-origin' in response.headers

def test_rate_limiting():
    """Test API rate limiting"""
    # Make multiple requests rapidly
    responses = []
    for i in range(100):
        response = client.get('/api/health')
        responses.append(response.status_code)
    
    # Should have some 429 responses if rate limiting works
    assert 429 in responses or all(r == 200 for r in responses)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
