# Contributing to TrustGraph Engine

Thank you for your interest in contributing to the TrustGraph Engine! This project is part of NITI Aayog's Digital ShramSetu initiative to empower India's 490 million informal workers.

## 🇮🇳 Mission Alignment

All contributions should align with our core mission:
- **Financial Inclusion**: Empowering informal workers with digital identity
- **Voice-First Design**: Accessible interfaces for low-literacy users
- **Privacy Protection**: DPDP Act 2023 compliance and data sovereignty
- **Viksit Bharat 2047**: Contributing to India's development goals

## 🚀 Development Workflow

### 1. Getting Started
```bash
# Fork the repository
git clone https://github.com/your-username/trustgraph-engine.git
cd trustgraph-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### 2. Development Standards
Follow our [Development Standards](.kiro/steering/trustgraph-development-standards.md):

- **Python 3.11+** for all code
- **AWS-native** serverless architecture
- **Voice-first** interface design
- **DPDP Act 2023** compliance
- **Test coverage >90%**

### 3. Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/ --cov=src --cov-report=html
```

## 📝 Contribution Types

### 🐛 Bug Reports
Use the bug report template and include:
- **Environment**: AWS region, Python version, dependencies
- **Steps to reproduce**: Clear, minimal example
- **Expected vs actual behavior**
- **Impact**: How it affects informal workers or system functionality

### ✨ Feature Requests
Consider these priorities:
1. **Voice Interface**: Multi-language support improvements
2. **Financial Integration**: New banking/payment partnerships
3. **Accessibility**: Features for differently-abled users
4. **Regional Adaptation**: State-specific requirements

### 🔧 Code Contributions

#### Pull Request Process
1. **Create feature branch**: `git checkout -b feature/voice-hindi-improvement`
2. **Implement changes** following our standards
3. **Add comprehensive tests** with >90% coverage
4. **Update documentation** including API docs
5. **Submit PR** with detailed description

#### PR Template
```markdown
## Description
Brief description of changes and motivation

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Compliance
- [ ] DPDP Act 2023 compliance verified
- [ ] Voice accessibility tested
- [ ] AWS security best practices followed

## Impact on Informal Workers
Describe how this change benefits the target users
```

## 🏗️ Architecture Guidelines

### AWS Services Usage
```yaml
Preferred Services:
  compute: AWS Lambda (serverless-first)
  database: Amazon Neptune (graph), DynamoDB (NoSQL)
  storage: Amazon S3 (encrypted)
  ai_ml: Amazon SageMaker, Transcribe, Polly
  security: AWS KMS, IAM, Secrets Manager

Regional Requirements:
  primary: ap-south-1 (Mumbai, India)
  backup: ap-southeast-1 (Singapore)
  data_residency: Indian data stays in India
```

### Voice-First Design Principles
- **Primary Interface**: Voice commands in local languages
- **Fallback UI**: Simple visual confirmation/error handling
- **Accessibility**: Screen reader compatible
- **Offline Capability**: Core functions work without internet

### Security & Privacy
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Authentication**: Aadhaar OTP + voice biometric
- **Data Minimization**: Collect only essential information
- **Consent Management**: Granular permissions in user's language

## 🧪 Testing Guidelines

### Test Categories
```python
# Unit Tests - Business logic
def test_trust_score_calculation():
    """Test GNN-based trust scoring algorithm"""
    pass

# Integration Tests - AWS services
def test_voice_processing_pipeline():
    """Test Bhashini API + Transcribe integration"""
    pass

# End-to-End Tests - User journeys
def test_worker_onboarding_flow():
    """Test complete worker registration in Hindi"""
    pass

# Performance Tests - Scale requirements
def test_concurrent_user_handling():
    """Test 10M+ concurrent users simulation"""
    pass
```

### Test Data
- Use **synthetic data** for testing
- **No real Aadhaar numbers** or personal information
- **Anonymized** voice samples for audio testing
- **Mock APIs** for external service integration

## 📚 Documentation Standards

### Code Documentation
```python
def process_voice_command(audio_data: bytes, source_lang: str) -> dict:
    """
    Process voice command in Indian languages.
    
    Args:
        audio_data: Raw audio bytes from user
        source_lang: ISO 639-1 language code (hi, bn, te, etc.)
    
    Returns:
        dict: {
            'transcribed_text': str,
            'intent': str,
            'confidence': float,
            'response_text': str,
            'response_audio': bytes
        }
    
    Raises:
        VoiceProcessingError: If audio quality is insufficient
        LanguageNotSupportedError: If language not in supported list
    
    Example:
        >>> result = process_voice_command(audio_bytes, 'hi')
        >>> print(result['transcribed_text'])
        'मुझे काम का प्रमाणपत्र चाहिए'
    """
```

### API Documentation
- **OpenAPI 3.0** specifications for all endpoints
- **Multi-language** examples (Hindi, English, regional languages)
- **Error codes** with user-friendly messages
- **Rate limiting** and authentication details

## 🌍 Localization & Accessibility

### Language Support
Priority languages based on informal worker demographics:
1. **Hindi** (40% of informal workers)
2. **Bengali** (8% of informal workers)
3. **Telugu** (7% of informal workers)
4. **Marathi** (6% of informal workers)
5. **Tamil** (5% of informal workers)

### Accessibility Requirements
- **Voice-first** design for low-literacy users
- **High contrast** visual elements
- **Large fonts** and simple layouts
- **Screen reader** compatibility
- **Offline functionality** for poor connectivity areas

## 🔒 Security & Compliance

### DPDP Act 2023 Compliance
- **Data localization**: Indian data in ap-south-1 only
- **Consent management**: Granular permissions
- **Right to erasure**: User data deletion capabilities
- **Audit trails**: Immutable blockchain logs

### Security Best Practices
- **Zero-trust architecture**
- **Principle of least privilege**
- **Regular security audits**
- **Vulnerability scanning** in CI/CD
- **Incident response** procedures

## 🤝 Community Guidelines

### Code of Conduct
- **Respectful communication** in all interactions
- **Inclusive language** considering diverse backgrounds
- **Focus on mission**: Empowering informal workers
- **Constructive feedback** in code reviews

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Technical questions and ideas
- **Pull Requests**: Code contributions and reviews

## 🏆 Recognition

Contributors will be recognized for:
- **Code contributions** with significant impact
- **Documentation improvements**
- **Community support** and mentoring
- **Accessibility enhancements**
- **Regional adaptation** efforts

### Contributor Levels
- **Contributor**: Merged pull requests
- **Regular Contributor**: 5+ merged PRs
- **Core Contributor**: 20+ merged PRs + code reviews
- **Maintainer**: Trusted with repository access

## 📞 Getting Help

### Technical Support
- **Documentation**: Check existing docs first
- **GitHub Issues**: Search existing issues
- **Discussions**: Ask questions in GitHub Discussions

### Mentorship
New contributors can request mentorship for:
- **First-time contributions**
- **Complex feature development**
- **AWS architecture guidance**
- **Voice interface development**

---

## 🙏 Thank You

Your contributions help empower 490 million informal workers in India and support the Viksit Bharat 2047 vision. Every line of code, documentation improvement, and bug fix makes a difference in someone's life.

**Together, we're building a more inclusive digital economy for India! 🇮🇳**