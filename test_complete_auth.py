"""
Test Complete Authentication Flow
Tests signup, login, OTP verification, profile management
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)
    print(f"{'='*60}\n")

def test_signup_flow():
    """Test complete signup flow"""
    print("\n[TEST 1] SIGNUP FLOW")
    print("-" * 60)
    
    # Step 1: Signup
    signup_data = {
        "phone": "9876543210",
        "aadhaar_number": "123456789012",
        "name": "Ram Kumar",
        "email": "ram@example.com",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "preferred_language": "hi"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
    print_response("1.1 Signup Request", response)
    
    if response.status_code == 200:
        data = response.json()
        otp = data.get('otp_demo')
        signup_data_returned = data.get('signup_data')
        
        if otp:
            print(f"[OK] OTP Generated: {otp}")
            
            # Step 2: Verify OTP
            time.sleep(1)
            verify_data = {
                "phone": signup_data['phone'],
                "otp": otp,
                "signup_data": signup_data_returned
            }
            
            response = requests.post(f"{BASE_URL}/api/auth/signup/verify", json=verify_data)
            print_response("1.2 Verify Signup OTP", response)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                user_id = data.get('user_profile', {}).get('user_id')
                print(f"[OK] Signup Complete!")
                print(f"   Token: {token[:50]}...")
                print(f"   User ID: {user_id}")
                return token, user_id
    
    return None, None

def test_login_flow():
    """Test complete login flow"""
    print("\n[TEST 2] LOGIN FLOW")
    print("-" * 60)
    
    # Step 1: Login
    login_data = {
        "phone": "9876543210"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print_response("2.1 Login Request", response)
    
    if response.status_code == 200:
        data = response.json()
        otp = data.get('otp_demo')
        
        if otp:
            print(f"[OK] OTP Generated: {otp}")
            
            # Step 2: Verify OTP
            time.sleep(1)
            verify_data = {
                "phone": login_data['phone'],
                "otp": otp
            }
            
            response = requests.post(f"{BASE_URL}/api/auth/login/verify", json=verify_data)
            print_response("2.2 Verify Login OTP", response)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                user_id = data.get('user_profile', {}).get('user_id')
                print(f"[OK] Login Complete!")
                print(f"   Token: {token[:50]}...")
                print(f"   User ID: {user_id}")
                return token, user_id
    
    return None, None

def test_profile_management(user_id, token):
    """Test profile get and update"""
    print("\n[TEST 3] PROFILE MANAGEMENT")
    print("-" * 60)
    
    # Step 1: Get Profile
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/profile/{user_id}", headers=headers)
    print_response("3.1 Get Profile", response)
    
    # Step 2: Update Profile
    update_data = {
        "address": "123 Main Street, Connaught Place",
        "city": "New Delhi",
        "pincode": "110002"
    }
    
    response = requests.put(
        f"{BASE_URL}/api/auth/profile/{user_id}",
        json=update_data,
        headers=headers
    )
    print_response("3.2 Update Profile", response)
    
    # Step 3: Get Updated Profile
    response = requests.get(f"{BASE_URL}/api/auth/profile/{user_id}", headers=headers)
    print_response("3.3 Get Updated Profile", response)

def test_aadhaar_verification(user_id, token):
    """Test Aadhaar verification"""
    print("\n[TEST 4] AADHAAR VERIFICATION")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    verify_data = {
        "otp": "123456"  # Simulated OTP
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/aadhaar/verify/{user_id}",
        json=verify_data,
        headers=headers
    )
    print_response("4.1 Verify Aadhaar", response)

def test_api_docs():
    """Test API documentation"""
    print("\n[TEST 5] API DOCUMENTATION")
    print("-" * 60)
    
    response = requests.get(f"{BASE_URL}/docs")
    print(f"API Docs: {response.status_code == 200 and '[OK] Available' or '[X] Not Available'}")
    print(f"URL: {BASE_URL}/docs")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TrustGraph Engine - Complete Authentication Test Suite")
    print("="*60)
    
    try:
        # Test health
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("[X] Server not running!")
            return
        print("[OK] Server is running")
        
        # Test signup flow
        token, user_id = test_signup_flow()
        
        if not token:
            print("\n[!] Signup failed, trying login with existing user...")
            # Test login flow
            token, user_id = test_login_flow()
        
        if token and user_id:
            # Test profile management
            test_profile_management(user_id, token)
            
            # Test Aadhaar verification
            test_aadhaar_verification(user_id, token)
        
        # Test API docs
        test_api_docs()
        
        print("\n" + "="*60)
        print("[OK] ALL TESTS COMPLETED")
        print("="*60)
        print(f"\n[*] View API Documentation: {BASE_URL}/docs")
        print(f"[*] View Homepage: {BASE_URL}")
        print(f"[*] Health Check: {BASE_URL}/api/health")
        
    except requests.exceptions.ConnectionError:
        print("\n[X] Cannot connect to server!")
        print("Make sure the server is running: python app.py")
    except Exception as e:
        print(f"\n[X] Test failed: {e}")

if __name__ == "__main__":
    main()
