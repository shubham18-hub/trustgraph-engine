"""
Test Authentication Flow
Quick test to verify signup and login work correctly
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api"

def test_signup():
    """Test complete signup flow"""
    print("\n" + "="*60)
    print("TEST 1: SIGNUP FLOW")
    print("="*60)
    
    # Step 1: Initiate signup
    print("\n[1/2] Initiating signup...")
    signup_data = {
        "phone": "9876543210",
        "aadhaar_number": "123456789012",
        "name": "Test User",
        "email": "test@example.com",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "preferred_language": "hi"
    }
    
    response = requests.post(f"{API_BASE}/auth/signup", json=signup_data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if not result.get('success'):
        print("❌ Signup initiation failed!")
        return None
    
    print("✓ OTP sent successfully!")
    otp = result.get('otp_demo')
    print(f"OTP: {otp}")
    
    # Step 2: Verify OTP
    print("\n[2/2] Verifying OTP...")
    verify_data = {
        "phone": signup_data['phone'],
        "otp": otp,
        "signup_data": result.get('signup_data')
    }
    
    response = requests.post(f"{API_BASE}/auth/signup/verify", json=verify_data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print("✓ Signup completed successfully!")
        return result.get('token'), result.get('user_profile')
    else:
        print("❌ OTP verification failed!")
        return None

def test_login():
    """Test complete login flow"""
    print("\n" + "="*60)
    print("TEST 2: LOGIN FLOW")
    print("="*60)
    
    # Step 1: Initiate login
    print("\n[1/2] Initiating login...")
    login_data = {
        "phone": "9876543210"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if not result.get('success'):
        print("❌ Login initiation failed!")
        return None
    
    print("✓ OTP sent successfully!")
    otp = result.get('otp_demo')
    print(f"OTP: {otp}")
    
    # Step 2: Verify OTP
    print("\n[2/2] Verifying OTP...")
    verify_data = {
        "phone": login_data['phone'],
        "otp": otp
    }
    
    response = requests.post(f"{API_BASE}/auth/login/verify", json=verify_data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print("✓ Login completed successfully!")
        return result.get('token'), result.get('user_profile')
    else:
        print("❌ OTP verification failed!")
        return None

def test_profile(token, user_id):
    """Test profile retrieval"""
    print("\n" + "="*60)
    print("TEST 3: GET PROFILE")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/auth/profile/{user_id}", headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        print("✓ Profile retrieved successfully!")
    else:
        print("❌ Profile retrieval failed!")

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST 0: HEALTH CHECK")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get('status') == 'healthy':
            print("✓ Server is healthy!")
            return True
        else:
            print("❌ Server is not healthy!")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TrustGraph Engine - Authentication Flow Test")
    print("="*60)
    
    # Test health
    if not test_health():
        print("\n❌ Server is not running. Please start the server first.")
        print("Run: python app.py")
        exit(1)
    
    # Test signup
    result = test_signup()
    if result:
        token, user_profile = result
        user_id = user_profile.get('user_id')
        
        # Wait a bit
        time.sleep(1)
        
        # Test profile
        test_profile(token, user_id)
        
        # Wait a bit
        time.sleep(1)
        
        # Test login
        test_login()
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)
    print("\nYou can now:")
    print("1. Open http://localhost:8000 in your browser")
    print("2. Click 'Get Started' to go to auth page")
    print("3. Try signup or login with the UI")
    print("="*60 + "\n")
