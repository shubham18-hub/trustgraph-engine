"""
TrustGraph Engine - Simple Demo Server
Works without full dependencies - demonstrates core features
"""

import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

PORT = 8080

class TrustGraphHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP handler for TrustGraph demo"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve static files
        if path == '/':
            # Serve root index.html
            if os.path.exists('index.html'):
                self.serve_file('index.html', 'text/html')
            else:
                self.send_demo_page()
        elif path == '/index.html':
            if os.path.exists('index.html'):
                self.serve_file('index.html', 'text/html')
            else:
                self.send_demo_page()
        elif path.startswith('/frontend/'):
            file_path = path[1:]  # Remove leading /
            if os.path.exists(file_path):
                content_type = self.guess_type(file_path)
                self.serve_file(file_path, content_type)
            else:
                self.send_error(404)
        elif path == '/api/health':
            self.send_json_response({
                'status': 'healthy',
                'message': 'TrustGraph Engine Demo Server',
                'version': '1.0.0',
                'timestamp': '2026-03-05T10:00:00Z',
                'services': {
                    'api': 'operational',
                    'blockchain': 'operational',
                    'voice_ai': 'operational',
                    'database': 'operational'
                }
            })
        elif path.startswith('/demo/worker/'):
            worker_id = path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'worker_id': worker_id,
                'profile': {
                    'name': 'Rajesh Kumar',
                    'did': f'did:india:worker:{worker_id[:16]}',
                    'trust_score': 720,
                    'skills': ['Mason', 'Plumber', 'Electrician'],
                    'languages': ['Hindi', 'English', 'Punjabi'],
                    'location': 'Delhi, India',
                    'experience_years': 8,
                    'verified': True
                },
                'credentials_count': 5,
                'total_earnings': 125000,
                'completed_jobs': 42
            })
        elif path == '/api/v1/analytics/demographics':
            self.send_json_response({
                'success': True,
                'total_workers': 1250000,
                'states_covered': 22,
                'top_states': [
                    {'state': 'Uttar Pradesh', 'workers': 285000, 'percentage': 22.8},
                    {'state': 'Maharashtra', 'workers': 198000, 'percentage': 15.8},
                    {'state': 'Bihar', 'workers': 156000, 'percentage': 12.5},
                    {'state': 'West Bengal', 'workers': 142000, 'percentage': 11.4},
                    {'state': 'Madhya Pradesh', 'workers': 98000, 'percentage': 7.8}
                ],
                'languages_distribution': {
                    'Hindi': 45.2,
                    'Bengali': 12.8,
                    'Telugu': 9.5,
                    'Marathi': 8.3,
                    'Tamil': 7.1
                },
                'avg_trust_score': 685,
                'timestamp': '2026-03-05T10:00:00Z'
            })
        elif path.startswith('/api/trust-score/'):
            worker_id = path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'worker_id': worker_id,
                'resilience_score': 720,
                'category': 'good',
                'confidence': 0.85,
                'factors': {
                    'work_consistency': {'score': 750, 'weight': 0.30},
                    'payment_history': {'score': 800, 'weight': 0.25},
                    'employer_ratings': {'score': 680, 'weight': 0.20},
                    'skill_verification': {'score': 700, 'weight': 0.15},
                    'social_proof': {'score': 650, 'weight': 0.10}
                },
                'credit_eligibility': {
                    'eligible': True,
                    'max_loan_amount': 50000,
                    'interest_rate': 15.0,
                    'category': 'Standard'
                },
                'recommendations': [
                    'Complete more work assignments regularly',
                    'Request ratings from employers'
                ]
            })
        elif path.startswith('/api/wallet/'):
            worker_id = path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'wallet': {
                    'wallet_id': f'wallet_{worker_id}',
                    'worker_id': worker_id,
                    'did': f'did:india:worker:{worker_id[:16]}',
                    'reputation_assets': {
                        'credentials_count': 5,
                        'trust_score': 720,
                        'trust_category': 'Good'
                    },
                    'financial_summary': {
                        'total_earnings': 125000,
                        'completed_transactions': 12,
                        'pending_payments': 2
                    },
                    'verified_skills': ['Mason', 'Plumber', 'Electrician']
                }
            })
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except:
            data = {}
        
        if path == '/api/v1/workers/register':
            self.send_json_response({
                'success': True,
                'message': 'Worker registered successfully',
                'worker_id': f'worker_{int(time.time())}',
                'did': f'did:india:worker:{hex(int(time.time()))[2:]}',
                'blockchain_tx': f'0x{hex(int(time.time()))[2:]}abc123',
                'voice_kyc_status': 'verified',
                'aadhaar_verified': True,
                'timestamp': '2026-03-05T10:00:00Z'
            })
        elif path == '/api/v1/blockchain/verify-credential':
            self.send_json_response({
                'success': True,
                'verified': True,
                'credential_id': data.get('credential_id', 'cred_demo123'),
                'issuer': 'TrustGraph Authority',
                'blockchain_proof': f'0x{hex(int(time.time()))[2:]}verified',
                'issued_date': '2024-01-15T10:00:00Z',
                'expiry_date': '2027-01-15T10:00:00Z',
                'verification_timestamp': '2026-03-05T10:00:00Z',
                'trust_level': 'high'
            })
        elif path.endswith('/calculate'):
            worker_id = path.split('/')[-2]
            self.send_json_response({
                'success': True,
                'message': 'Trust score calculated successfully',
                'worker_id': worker_id,
                'resilience_score': 720,
                'category': 'good',
                'calculated_at': '2026-03-04T10:00:00Z'
            })
        elif path == '/api/contracts/create':
            self.send_json_response({
                'success': True,
                'contract_id': 'contract_demo123',
                'message': 'Smart contract created successfully',
                'blockchain_hash': 'abc123def456...'
            })
        elif 'submit-proof' in path:
            self.send_json_response({
                'success': True,
                'proof_id': 'proof_demo123',
                'auto_verified': True,
                'payment_initiated': True,
                'payment_id': 'pay_demo123',
                'message': 'Milestone verified and payment initiated automatically'
            })
        else:
            self.send_json_response({
                'success': True,
                'message': 'Demo endpoint - feature integrated',
                'note': 'Install full dependencies for complete functionality'
            })
    
    def serve_file(self, filepath, content_type):
        """Serve a file"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
    
    def send_json_response(self, data):
        """Send JSON response"""
        response = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)
    
    def send_demo_page(self):
        """Send demo HTML page"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrustGraph Engine - Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #FF9933 0%, #138808 100%);
            color: white;
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-size: 3rem; margin-bottom: 1rem; text-align: center; }
        .subtitle { font-size: 1.5rem; text-align: center; margin-bottom: 3rem; opacity: 0.9; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 3rem 0; }
        .feature-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .feature-card h3 { font-size: 1.5rem; margin-bottom: 1rem; }
        .feature-card p { opacity: 0.9; line-height: 1.6; }
        .api-section {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
        }
        .api-endpoint {
            background: rgba(0,0,0,0.3);
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            font-family: 'Courier New', monospace;
        }
        .btn {
            display: inline-block;
            padding: 1rem 2rem;
            background: white;
            color: #FF9933;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            margin: 0.5rem;
            transition: transform 0.3s;
        }
        .btn:hover { transform: translateY(-2px); }
        .status { text-align: center; margin: 2rem 0; }
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1.5rem;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            margin: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🇮🇳 TrustGraph Engine</h1>
        <div class="subtitle">Digital ShramSetu - Empowering 490 Million Workers</div>
        
        <div class="status">
            <div class="status-badge">✓ Demo Server Running</div>
            <div class="status-badge">✓ All Features Integrated</div>
            <div class="status-badge">✓ APIs Active</div>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <h3>📊 Trust Score</h3>
                <p>Resilience Score using GNN-based reputation analysis. Converts social proof into bankable credit score.</p>
            </div>
            
            <div class="feature-card">
                <h3>💼 Digital Wallet</h3>
                <p>Self-sovereign identity wallet storing W3C Verifiable Credentials. You own your reputation assets.</p>
            </div>
            
            <div class="feature-card">
                <h3>📝 Smart Contracts</h3>
                <p>Agentic milestone-based contracts with auto-payment on verification. 100% wage security.</p>
            </div>
            
            <div class="feature-card">
                <h3>🎤 Voice Interface</h3>
                <p>22 Indian languages via Bhashini. Zero-barrier accessibility for all workers.</p>
            </div>
            
            <div class="feature-card">
                <h3>🔐 Authentication</h3>
                <p>Aadhaar-based authentication with OTP verification. DPDP Act 2023 compliant.</p>
            </div>
            
            <div class="feature-card">
                <h3>💰 UPI Payments</h3>
                <p>Instant milestone-based payments via UPI. No delays, no middlemen.</p>
            </div>
        </div>
        
        <div class="api-section">
            <h2 style="margin-bottom: 1rem;">Try the APIs</h2>
            <div class="api-endpoint">GET /api/health</div>
            <div class="api-endpoint">GET /api/trust-score/user_123</div>
            <div class="api-endpoint">POST /api/trust-score/user_123/calculate</div>
            <div class="api-endpoint">GET /api/wallet/user_123</div>
            <div class="api-endpoint">POST /api/contracts/create</div>
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/api/health" class="btn">Health Check</a>
            <a href="/api/trust-score/user_123" class="btn">Test Trust Score</a>
            <a href="/api/wallet/user_123" class="btn">Test Wallet</a>
            <a href="/frontend/" class="btn">Dashboard</a>
        </div>
        
        <div style="text-align: center; margin-top: 3rem; opacity: 0.8;">
            <p>Part of Viksit Bharat 2047 Initiative</p>
            <p style="margin-top: 0.5rem;">Built with ❤️ for India's workforce</p>
        </div>
    </div>
</body>
</html>
        """
        response = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    """Start demo server"""
    print("=" * 60)
    print("TrustGraph Engine - Demo Server")
    print("=" * 60)
    print()
    print("🇮🇳 Digital ShramSetu - Empowering 490M Workers")
    print()
    print("Features Integrated:")
    print("  ✓ Trust Score (Resilience Score)")
    print("  ✓ Digital Wallet (Self-Sovereign Identity)")
    print("  ✓ Milestone Contracts (Smart Contracts)")
    print("  ✓ Voice Interface (22 Languages)")
    print("  ✓ Authentication (Aadhaar + OTP)")
    print()
    print(f"Server starting on port {PORT}...")
    print()
    print("Access:")
    print(f"  Landing Page:  http://localhost:{PORT}/")
    print(f"  Dashboard:     http://localhost:{PORT}/frontend/")
    print(f"  Health Check:  http://localhost:{PORT}/api/health")
    print()
    print("Demo API Endpoints:")
    print(f"  GET  http://localhost:{PORT}/api/trust-score/user_123")
    print(f"  POST http://localhost:{PORT}/api/trust-score/user_123/calculate")
    print(f"  GET  http://localhost:{PORT}/api/wallet/user_123")
    print(f"  POST http://localhost:{PORT}/api/contracts/create")
    print()
    print("Note: This is a demo server showing integrated features.")
    print("      Install full dependencies for complete functionality.")
    print("      See: FINAL_SETUP_INSTRUCTIONS.txt")
    print()
    print("=" * 60)
    print("Press Ctrl+C to stop server")
    print("=" * 60)
    print()
    
    try:
        with socketserver.TCPServer(("", PORT), TrustGraphHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        print("Thank you for using TrustGraph Engine!")

if __name__ == "__main__":
    main()
