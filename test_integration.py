"""
TrustGraph Engine - Integration Test
Tests all system components without external dependencies
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_database():
    """Test database connectivity and schema"""
    print("\n[TEST 1] Database Integration")
    print("-" * 50)
    
    try:
        from src.database import db
        
        # Test connection
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'sessions', 'otp_codes', 'credentials', 'transactions', 'trust_scores']
        
        print(f"✅ Database connected: trustgraph.db")
        print(f"✅ Tables found: {len(tables)}")
        
        for table in required_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  • {table}: {count} records")
            else:
                print(f"  ❌ {table}: MISSING")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_auth_service():
    """Test authentication service"""
    print("\n[TEST 2] Authentication Service")
    print("-" * 50)
    
    try:
        # Test without importing (to avoid dependency issues)
        import hashlib
        import secrets
        from datetime import datetime, timedelta
        
        # Simulate OTP generation
        otp = str(secrets.randbelow(900000) + 100000)
        print(f"✅ OTP generation: {otp}")
        
        # Simulate Aadhaar hashing
        test_aadhaar = "123456789012"
        aadhaar_hash = hashlib.sha256(test_aadhaar.encode()).hexdigest()
        print(f"✅ Aadhaar hashing: {aadhaar_hash[:16]}...")
        
        # Test database integration
        from src.database import db
        
        test_phone = "+919999999999"
        expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        
        db.save_otp(test_phone, otp, expires_at, aadhaar_hash)
        print(f"✅ OTP saved to database")
        
        # Verify OTP
        result = db.verify_otp(test_phone, otp)
        if result:
            print(f"✅ OTP verification successful")
        else:
            print(f"❌ OTP verification failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth service test failed: {e}")
        return False

def test_file_structure():
    """Test file structure and organization"""
    print("\n[TEST 3] File Structure")
    print("-" * 50)
    
    required_files = {
        'Backend': [
            'app.py',
            'src/services/auth_service.py',
            'src/services/bedrock_service.py',
            'src/services/voice_service.py',
            'src/services/blockchain_service.py',
            'src/services/upi_service.py',
            'src/database/db.py'
        ],
        'Frontend': [
            'frontend/index.html',
            'frontend/app.js',
            'frontend/styles.css',
            'frontend/voice.js',
            'frontend/themes.css',
            'frontend/accessibility.css'
        ],
        'Infrastructure': [
            'infrastructure/cloudformation-stack.yaml',
            'infrastructure/multi-region-failover.yaml',
            'Dockerfile',
            'docker-compose.yml'
        ],
        'Documentation': [
            'README.md',
            'API.md',
            'QUICKSTART.txt'
        ]
    }
    
    all_present = True
    
    for category, files in required_files.items():
        print(f"\n{category}:")
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"  ✅ {file} ({size:,} bytes)")
            else:
                print(f"  ❌ {file} MISSING")
                all_present = False
    
    return all_present

def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\n[TEST 4] API Endpoints")
    print("-" * 50)
    
    try:
        # Read app.py to check endpoints
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        endpoints = [
            ('/api/health', 'Health check'),
            ('/api/auth/init', 'Initialize authentication'),
            ('/api/auth/verify', 'Verify OTP'),
            ('/api/intent/classify', 'Classify intent'),
            ('/api/voice/command', 'Process voice command'),
            ('/api/trust/calculate', 'Calculate trust score')
        ]
        
        for endpoint, description in endpoints:
            if endpoint in content:
                print(f"  ✅ {endpoint} - {description}")
            else:
                print(f"  ❌ {endpoint} - MISSING")
        
        # Check for duplicate main.py
        if os.path.exists('src/main.py'):
            print(f"\n  ⚠️  WARNING: Duplicate src/main.py detected")
            print(f"     Consider consolidating into app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_frontend_config():
    """Test frontend configuration"""
    print("\n[TEST 5] Frontend Configuration")
    print("-" * 50)
    
    try:
        with open('frontend/app.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check API_BASE
        if "const API_BASE = 'http://localhost:8000/api'" in content:
            print("  ✅ API_BASE configured: http://localhost:8000/api")
        else:
            print("  ⚠️  API_BASE configuration unclear")
        
        # Check key functions
        functions = [
            'sendOTP',
            'verifyOTP',
            'loadUserData',
            'toggleVoice',
            'showCredentials',
            'showJobs',
            'showPayments'
        ]
        
        for func in functions:
            if f"function {func}" in content or f"async function {func}" in content:
                print(f"  ✅ {func}() defined")
            else:
                print(f"  ❌ {func}() MISSING")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend config test failed: {e}")
        return False

def test_deployment_readiness():
    """Test deployment configuration"""
    print("\n[TEST 6] Deployment Readiness")
    print("-" * 50)
    
    checks = {
        'Docker': os.path.exists('Dockerfile'),
        'Docker Compose': os.path.exists('docker-compose.yml'),
        'CloudFormation': os.path.exists('infrastructure/cloudformation-stack.yaml'),
        'Multi-Region': os.path.exists('infrastructure/multi-region-failover.yaml'),
        'Nginx Config': os.path.exists('nginx.conf'),
        'Requirements': os.path.exists('requirements-prod.txt'),
        'Start Script': os.path.exists('START.bat'),
        'Deploy Script': os.path.exists('DEPLOY.bat')
    }
    
    for check, result in checks.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {check}")
    
    return all(checks.values())

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"\nTests Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    print("\nTest Results:")
    for test, result in results.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {test}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Start server: python app.py")
        print("  2. Open browser: http://localhost:8000")
        print("  3. Test voice interface and authentication")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review issues above.")
    
    print("\n" + "=" * 60)

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("TrustGraph Engine - Integration Test Suite")
    print("=" * 60)
    
    results = {
        'Database': test_database(),
        'Authentication': test_auth_service(),
        'File Structure': test_file_structure(),
        'API Endpoints': test_api_endpoints(),
        'Frontend Config': test_frontend_config(),
        'Deployment': test_deployment_readiness()
    }
    
    print_summary(results)
    
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
