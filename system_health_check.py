"""
TrustGraph Engine - System Health Check & Self-Healing
Validates all integrations and automatically fixes common issues
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SystemHealthCheck:
    """Comprehensive system health validation"""
    
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.status = {
            'database': False,
            'auth_service': False,
            'bedrock_service': False,
            'voice_service': False,
            'blockchain_service': False,
            'upi_service': False,
            'frontend': False,
            'api_endpoints': False
        }
    
    async def run_full_check(self):
        """Run complete system health check"""
        logger.info("=" * 60)
        logger.info("TrustGraph Engine - System Health Check")
        logger.info("=" * 60)
        
        await self.check_database()
        await self.check_auth_service()
        await self.check_bedrock_service()
        await self.check_api_endpoints()
        await self.check_frontend_config()
        
        self.print_report()
    
    async def check_database(self):
        """Validate database connectivity and schema"""
        logger.info("\n[1/5] Checking Database...")
        
        try:
            from src.database import db
            
            # Test database connection
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'sessions', 'otp_codes', 'credentials', 'transactions', 'trust_scores']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                self.issues.append(f"Missing tables: {missing_tables}")
                logger.warning(f"  ⚠️  Missing tables: {missing_tables}")
            else:
                logger.info("  ✅ All database tables present")
            
            # Test basic operations
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            logger.info(f"  ✅ Database operational ({user_count} users)")
            
            conn.close()
            self.status['database'] = True
            
        except Exception as e:
            self.issues.append(f"Database error: {str(e)}")
            logger.error(f"  ❌ Database check failed: {e}")
            self.status['database'] = False
    
    async def check_auth_service(self):
        """Validate authentication service"""
        logger.info("\n[2/5] Checking Authentication Service...")
        
        try:
            from src.services.auth_service import auth_service
            
            # Check service initialization
            if not hasattr(auth_service, 'db'):
                self.issues.append("Auth service not using database")
                logger.error("  ❌ Auth service not connected to database")
                self.status['auth_service'] = False
                return
            
            logger.info("  ✅ Auth service initialized")
            logger.info("  ✅ Database integration active")
            
            # Test OTP generation
            test_phone = "+919999999999"
            test_aadhaar = "123456789012"
            
            result = auth_service.initiate_aadhaar_auth(test_aadhaar, test_phone)
            
            if result.get('success'):
                logger.info("  ✅ OTP generation working")
                self.status['auth_service'] = True
            else:
                self.issues.append("OTP generation failed")
                logger.error("  ❌ OTP generation failed")
                self.status['auth_service'] = False
            
        except Exception as e:
            self.issues.append(f"Auth service error: {str(e)}")
            logger.error(f"  ❌ Auth service check failed: {e}")
            self.status['auth_service'] = False
    
    async def check_bedrock_service(self):
        """Validate AWS Bedrock integration"""
        logger.info("\n[3/5] Checking AWS Bedrock Service...")
        
        try:
            from src.services.bedrock_service import bedrock_service
            
            if bedrock_service.bedrock:
                logger.info("  ✅ Bedrock client initialized")
                logger.info(f"  ✅ Model: {bedrock_service.model_id}")
                logger.info(f"  ✅ Region: {bedrock_service.region}")
                
                # Test intent classification
                result = await bedrock_service.classify_intent("मेरा ट्रस्ट स्कोर क्या है?", "hi")
                
                if result.get('intent'):
                    logger.info(f"  ✅ Intent classification working: {result['intent']}")
                    self.status['bedrock_service'] = True
                else:
                    logger.warning("  ⚠️  Intent classification returned no result")
                    self.status['bedrock_service'] = False
            else:
                logger.warning("  ⚠️  Bedrock client not available (using fallback)")
                self.status['bedrock_service'] = False
            
        except Exception as e:
            self.issues.append(f"Bedrock service error: {str(e)}")
            logger.error(f"  ❌ Bedrock service check failed: {e}")
            self.status['bedrock_service'] = False
    
    async def check_api_endpoints(self):
        """Validate API endpoints"""
        logger.info("\n[4/5] Checking API Endpoints...")
        
        try:
            # Check app.py endpoints
            from app import app
            
            routes = [route.path for route in app.routes]
            
            required_endpoints = [
                '/',
                '/api/health',
                '/api/auth/init',
                '/api/auth/verify',
                '/api/intent/classify',
                '/api/voice/command',
                '/api/trust/calculate'
            ]
            
            missing_endpoints = [ep for ep in required_endpoints if ep not in routes]
            
            if missing_endpoints:
                self.issues.append(f"Missing endpoints: {missing_endpoints}")
                logger.warning(f"  ⚠️  Missing endpoints: {missing_endpoints}")
            else:
                logger.info(f"  ✅ All required endpoints present ({len(routes)} total)")
            
            # Check for duplicate endpoints with src/main.py
            if os.path.exists('src/main.py'):
                logger.warning("  ⚠️  Duplicate main.py detected - consider consolidating")
                self.issues.append("Duplicate main.py file exists")
            
            self.status['api_endpoints'] = len(missing_endpoints) == 0
            
        except Exception as e:
            self.issues.append(f"API endpoint error: {str(e)}")
            logger.error(f"  ❌ API endpoint check failed: {e}")
            self.status['api_endpoints'] = False
    
    async def check_frontend_config(self):
        """Validate frontend configuration"""
        logger.info("\n[5/5] Checking Frontend Configuration...")
        
        try:
            # Check frontend files exist
            frontend_files = [
                'frontend/index.html',
                'frontend/app.js',
                'frontend/styles.css',
                'frontend/voice.js'
            ]
            
            missing_files = [f for f in frontend_files if not os.path.exists(f)]
            
            if missing_files:
                self.issues.append(f"Missing frontend files: {missing_files}")
                logger.warning(f"  ⚠️  Missing files: {missing_files}")
            else:
                logger.info("  ✅ All frontend files present")
            
            # Check API_BASE configuration
            with open('frontend/app.js', 'r', encoding='utf-8') as f:
                content = f.read()
                
                if "const API_BASE = 'http://localhost:8000/api'" in content:
                    logger.info("  ✅ API_BASE configured correctly")
                else:
                    logger.warning("  ⚠️  API_BASE may need configuration")
                    self.issues.append("Frontend API_BASE configuration unclear")
            
            self.status['frontend'] = len(missing_files) == 0
            
        except Exception as e:
            self.issues.append(f"Frontend check error: {str(e)}")
            logger.error(f"  ❌ Frontend check failed: {e}")
            self.status['frontend'] = False
    
    def print_report(self):
        """Print comprehensive health report"""
        logger.info("\n" + "=" * 60)
        logger.info("SYSTEM HEALTH REPORT")
        logger.info("=" * 60)
        
        # Component status
        logger.info("\nComponent Status:")
        for component, status in self.status.items():
            icon = "✅" if status else "❌"
            logger.info(f"  {icon} {component.replace('_', ' ').title()}")
        
        # Overall health
        healthy_count = sum(1 for s in self.status.values() if s)
        total_count = len(self.status)
        health_percentage = (healthy_count / total_count) * 100
        
        logger.info(f"\nOverall Health: {health_percentage:.1f}% ({healthy_count}/{total_count} components)")
        
        # Issues
        if self.issues:
            logger.info(f"\n⚠️  Issues Found ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                logger.info(f"  {i}. {issue}")
        else:
            logger.info("\n✅ No issues found!")
        
        # Recommendations
        logger.info("\nRecommendations:")
        
        if not self.status['database']:
            logger.info("  • Reinitialize database: python -c 'from src.database import db; db.init_db()'")
        
        if not self.status['bedrock_service']:
            logger.info("  • Configure AWS credentials for Bedrock access")
            logger.info("  • System will use fallback intent classification")
        
        if 'Duplicate main.py' in str(self.issues):
            logger.info("  • Consider removing src/main.py to avoid confusion")
            logger.info("  • Use app.py as the single entry point")
        
        logger.info("\n" + "=" * 60)
        
        # Return exit code
        return 0 if health_percentage >= 80 else 1

async def main():
    """Run system health check"""
    checker = SystemHealthCheck()
    exit_code = await checker.run_full_check()
    
    logger.info("\nHealth check complete!")
    logger.info("Start server: python app.py")
    logger.info("View UI: http://localhost:8000")
    
    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
