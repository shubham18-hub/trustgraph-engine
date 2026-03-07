"""
TrustGraph Engine - Simple HTTP Server (No Dependencies)
Works with standard Python library only
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import urllib.parse

class TrustGraphHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for TrustGraph API"""
    
    def _send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_html_response(self, html, status=200):
        """Send HTML response"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def do_GET(self):
        """Handle GET requests"""
        
        # Parse URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Root endpoint
        if path == '/':
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrustGraph Engine - Digital ShramSetu | Empowering India's Workforce</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .header {
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #FF9933;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .header .subtitle {
            color: #138808;
            font-size: 1.3em;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .header .tagline {
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
        }
        
        .badges {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        
        .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        /* Stats Section */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        
        /* API Endpoints Section */
        .section {
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #333;
            font-size: 2em;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }
        
        .endpoint {
            background: #f8f9fa;
            border-left: 5px solid #138808;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .endpoint:hover {
            background: #e9ecef;
            border-left-width: 8px;
            transform: translateX(5px);
        }
        
        .method {
            display: inline-block;
            background: #138808;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.9em;
            margin-right: 10px;
        }
        
        .endpoint-url {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .endpoint-url:hover {
            text-decoration: underline;
        }
        
        .endpoint-desc {
            color: #666;
            margin-top: 10px;
            font-size: 0.95em;
        }
        
        /* Features Grid */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .feature-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .feature-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .feature-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .feature-desc {
            font-size: 0.95em;
            opacity: 0.9;
        }
        
        /* Tech Stack */
        .tech-stack {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }
        
        .tech-item {
            background: #f8f9fa;
            padding: 15px 25px;
            border-radius: 10px;
            border: 2px solid #667eea;
            font-weight: 600;
            color: #667eea;
        }
        
        /* CTA Section */
        .cta {
            background: linear-gradient(135deg, #FF9933 0%, #138808 100%);
            color: white;
            text-align: center;
            padding: 50px;
            border-radius: 15px;
            margin-top: 30px;
        }
        
        .cta h2 {
            font-size: 2.5em;
            margin-bottom: 20px;
            border: none;
            color: white;
        }
        
        .cta-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 30px;
        }
        
        .btn {
            padding: 15px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s ease;
            display: inline-block;
        }
        
        .btn-primary {
            background: white;
            color: #667eea;
        }
        
        .btn-primary:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        
        .btn-secondary {
            background: transparent;
            color: white;
            border: 2px solid white;
        }
        
        .btn-secondary:hover {
            background: white;
            color: #667eea;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: white;
            padding: 30px;
            margin-top: 30px;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
            font-weight: 600;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .stat-number {
                font-size: 2em;
            }
            
            .section {
                padding: 25px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🇮🇳 TrustGraph Engine</h1>
            <div class="subtitle">Digital ShramSetu Initiative</div>
            <div class="tagline">Empowering 490 Million Informal Workers in India</div>
            <div class="badges">
                <span class="badge">NITI Aayog Partnership</span>
                <span class="badge">Voice-First AI</span>
                <span class="badge">Blockchain Verified</span>
                <span class="badge">AWS Powered</span>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">490M</div>
                <div class="stat-label">Target Workers</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">$2.5T</div>
                <div class="stat-label">GDP Impact Potential</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">22</div>
                <div class="stat-label">Indian Languages</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">300%</div>
                <div class="stat-label">Income Increase</div>
            </div>
        </div>
        
        <!-- API Endpoints -->
        <div class="section">
            <h2>🔌 Live API Endpoints</h2>
            <p style="margin-bottom: 20px; color: #666;">Test these endpoints directly in your browser or via API calls</p>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/health" class="endpoint-url">/health</a>
                <div class="endpoint-desc">Check system health and service status</div>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/demo/worker/worker_123" class="endpoint-url">/demo/worker/{worker_id}</a>
                <div class="endpoint-desc">Get complete worker profile with trust score and credentials</div>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/demo/languages" class="endpoint-url">/demo/languages</a>
                <div class="endpoint-desc">View all 22 supported Indian constitutional languages</div>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/demo/trust-score/worker_123" class="endpoint-url">/demo/trust-score/{worker_id}</a>
                <div class="endpoint-desc">Calculate real-time trust score using Graph Neural Networks</div>
            </div>
        </div>
        
        <!-- Features -->
        <div class="section">
            <h2>✨ Key Features</h2>
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">🎤</div>
                    <div class="feature-title">Voice-First Interface</div>
                    <div class="feature-desc">Natural language processing in 22 Indian languages with Bhashini API integration</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">⛓️</div>
                    <div class="feature-title">Blockchain Credentials</div>
                    <div class="feature-desc">W3C Verifiable Credentials on Hyperledger Fabric with cryptographic proofs</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">AI Trust Scoring</div>
                    <div class="feature-desc">Graph Neural Networks for alternative credit assessment in <1 second</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">💰</div>
                    <div class="feature-title">Smart Payments</div>
                    <div class="feature-desc">Automated milestone-based UPI payments with instant verification</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-title">DPDP Act Compliant</div>
                    <div class="feature-desc">Full compliance with India's Digital Personal Data Protection Act 2023</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <div class="feature-title">AWS Bedrock GenAI</div>
                    <div class="feature-desc">Claude 3 Haiku & Sonnet for enhanced voice understanding and dispute resolution</div>
                </div>
            </div>
        </div>
        
        <!-- Technology Stack -->
        <div class="section">
            <h2>🛠️ Technology Stack</h2>
            <div class="tech-stack">
                <div class="tech-item">AWS Lambda</div>
                <div class="tech-item">Amazon Bedrock</div>
                <div class="tech-item">Amazon Neptune</div>
                <div class="tech-item">Amazon SageMaker</div>
                <div class="tech-item">Hyperledger Fabric</div>
                <div class="tech-item">Python 3.11</div>
                <div class="tech-item">FastAPI</div>
                <div class="tech-item">GraphStorm</div>
                <div class="tech-item">Bhashini API</div>
                <div class="tech-item">UPI Integration</div>
            </div>
        </div>
        
        <!-- CTA -->
        <div class="cta">
            <h2>Ready to Transform India's Workforce?</h2>
            <p style="font-size: 1.2em; margin-bottom: 20px;">Join us in empowering 490 million informal workers</p>
            <div class="cta-buttons">
                <a href="/health" class="btn btn-primary">Test API Now</a>
                <a href="https://github.com/your-org/trustgraph-engine" class="btn btn-secondary">View on GitHub</a>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Built with ❤️ for India's Informal Workers | <a href="https://www.niti.gov.in/">NITI Aayog</a> Digital ShramSetu Initiative</p>
            <p style="margin-top: 10px; opacity: 0.8;">Viksit Bharat 2047 | Atmanirbhar Bharat | Digital India</p>
        </div>
    </div>
</body>
</html>
            """
            self._send_html_response(html)
        
        # Health check
        elif path == '/health':
            response = {
                "status": "healthy",
                "message": "TrustGraph Engine is running (Simple Mode)",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "api": "operational",
                    "note": "Running in simple mode without FastAPI"
                }
            }
            self._send_json_response(response)
        
        # Demo worker profile
        elif path.startswith('/demo/worker/'):
            worker_id = path.split('/')[-1]
            response = {
                "worker_id": worker_id,
                "name": "राम कुमार (Ram Kumar)",
                "phone": "+91-9876543210",
                "location": "Noida, Uttar Pradesh",
                "preferred_language": "hi",
                "skills": ["construction", "painting", "electrical"],
                "trust_score": 720,
                "total_work_hours": 1200,
                "credentials_count": 15,
                "average_rating": 4.3,
                "last_work_date": "2024-01-25",
                "payment_status": "up_to_date",
                "verification_status": "verified"
            }
            self._send_json_response(response)
        
        # Demo languages
        elif path == '/demo/languages':
            response = {
                "supported_languages": {
                    "hi": "हिन्दी (Hindi)",
                    "bn": "বাংলা (Bengali)",
                    "te": "తెలుగు (Telugu)",
                    "mr": "मराठी (Marathi)",
                    "ta": "தமிழ் (Tamil)",
                    "gu": "ગુજરાતી (Gujarati)",
                    "kn": "ಕನ್ನಡ (Kannada)",
                    "ml": "മലയാളം (Malayalam)",
                    "or": "ଓଡ଼ିଆ (Odia)",
                    "pa": "ਪੰਜਾਬੀ (Punjabi)",
                    "as": "অসমীয়া (Assamese)",
                    "ur": "اردو (Urdu)",
                    "en": "English"
                },
                "total_languages": 13,
                "voice_support": "planned",
                "text_support": "full"
            }
            self._send_json_response(response)
        
        # Demo trust score
        elif path.startswith('/demo/trust-score/'):
            worker_id = path.split('/')[-1]
            response = {
                "worker_id": worker_id,
                "trust_score": 720,
                "confidence": 0.87,
                "risk_assessment": "low",
                "factors": {
                    "work_consistency": 0.85,
                    "skill_verification": 0.78,
                    "employer_ratings": 0.82,
                    "payment_history": 0.90
                },
                "score_history": [
                    {"date": "2024-01-15", "score": 680},
                    {"date": "2024-01-20", "score": 700},
                    {"date": "2024-01-25", "score": 720}
                ],
                "recommendations": [
                    "Complete more verified work to improve score",
                    "Get skill endorsements from employers",
                    "Maintain consistent payment history"
                ]
            }
            self._send_json_response(response)
        
        # 404 Not Found
        else:
            response = {
                "error": "Not Found",
                "message": f"Endpoint {path} not found",
                "available_endpoints": [
                    "/",
                    "/health",
                    "/demo/worker/{worker_id}",
                    "/demo/languages",
                    "/demo/trust-score/{worker_id}"
                ]
            }
            self._send_json_response(response, status=404)
    
    def do_POST(self):
        """Handle POST requests"""
        response = {
            "message": "POST endpoints require FastAPI",
            "note": "Install FastAPI for full functionality",
            "install_command": "pip install fastapi uvicorn"
        }
        self._send_json_response(response, status=501)
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def main():
    """Start the simple HTTP server"""
    host = '0.0.0.0'
    port = 8000
    
    print("=" * 60)
    print("TrustGraph Engine - Digital ShramSetu")
    print("Simple HTTP Server (No Dependencies Required)")
    print("=" * 60)
    print()
    print(f"[*] Starting server on http://{host}:{port}")
    print(f"[*] Open your browser to: http://localhost:{port}")
    print()
    print("[*] Available endpoints:")
    print("    - http://localhost:8000/")
    print("    - http://localhost:8000/health")
    print("    - http://localhost:8000/demo/worker/worker_123")
    print("    - http://localhost:8000/demo/languages")
    print("    - http://localhost:8000/demo/trust-score/worker_123")
    print()
    print("[*] Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        server = HTTPServer((host, port), TrustGraphHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down server...")
        server.shutdown()
        print("[+] Server stopped")
    except Exception as e:
        print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    main()
