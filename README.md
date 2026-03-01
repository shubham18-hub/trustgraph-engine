# TrustGraph Engine - Working Prototype

> AI-powered intent classification and trust scoring system

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/trustgraph-engine.git
cd trustgraph-engine

# Run the server (no dependencies needed!)
python server_with_ui.py

# Open browser to http://localhost:8000
```

## ✨ Features

- **Hindi Intent Classification**: Recognizes 6 different intent types
- **Trust Score Calculation**: Demonstrates scoring algorithm
- **RESTful API**: JSON endpoints with CORS support
- **Modern UI**: Responsive design with smooth animations
- **Zero Dependencies**: Uses only Python standard library

## 🎯 Supported Intents

1. `CHECK_TRUST_SCORE` - Check credit/trust score
2. `ADD_WORK_RECORD` - Record completed work
3. `REQUEST_PAYMENT` - Request payment
4. `VERIFY_CREDENTIAL` - Verify certificate
5. `RAISE_DISPUTE` - Report issue
6. `GET_HELP` - Request assistance

## 🧪 Test Commands

Try these Hindi commands in the demo:

- `मेरा ट्रस्ट स्कोर क्या है?` (What is my trust score?)
- `काम पूरा हो गया` (Work completed)
- `मुझे पैसे चाहिए` (I need payment)
- `प्रमाणपत्र दिखाओ` (Show certificate)

## 📡 API Endpoints

### POST /api/intent/classify
```json
{
  "text": "मेरा ट्रस्ट स्कोर क्या है?",
  "language": "hi"
}
```

### POST /api/trust/calculate
```json
{
  "worker_id": "demo_123"
}
```

### GET /api/health
Check system status

## 🛠️ Tech Stack

- **Backend**: Python 3.x (standard library)
- **Frontend**: HTML5, CSS3, JavaScript
- **API**: RESTful with JSON
- **No external dependencies required**

## 📁 Project Structure

```
trustgraph-engine/
├── server_with_ui.py    # Complete backend server
├── index.html           # UI structure
├── styles.css           # Styling
├── script.js            # Frontend logic
├── README.md            # This file
└── LICENSE              # MIT License
```

## 🔧 How It Works

1. **Backend**: Python HTTP server serving both UI and API
2. **Intent Classification**: Rule-based pattern matching (80%+ accuracy)
3. **Frontend**: Modern UI with real-time API integration
4. **CORS Enabled**: Works with any frontend framework

## ⚠️ Disclaimer

This is a **technical prototype** for demonstration purposes:
- Uses rule-based classification (not ML)
- No database or data persistence
- Sample data only
- Not production-ready

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🤝 Contributing

This is a prototype project. For production use, consider:
- Adding ML-based classification
- Implementing database
- Adding authentication
- Security hardening
- Load testing

## 📞 Support

For issues or questions, please open a GitHub issue.

---

**Built as a technical demonstration of AI-powered intent classification**
