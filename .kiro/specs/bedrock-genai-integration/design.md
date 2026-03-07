# Design Document: AWS Bedrock GenAI Integration

## Overview

This design document specifies the integration of AWS Bedrock GenAI capabilities into the TrustGraph Engine (Digital ShramSetu initiative). The integration enhances the platform's ability to serve India's 490 million informal workers through five key GenAI-powered features: enhanced voice intent understanding, intelligent dispute resolution, personalized voice guidance, skill certificate analysis, and fraud detection.

The design maintains full compliance with the Digital Personal Data Protection Act 2023 (DPDP Act), ensures data residency in ap-south-1 (Mumbai), and optimizes costs through intelligent model selection and caching strategies.

### Design Goals

1. **Enhanced User Experience**: Improve voice interaction quality for low-literacy workers across 22 Indian languages
2. **Intelligent Automation**: Automate dispute resolution and document verification with AI-powered analysis
3. **Cost Efficiency**: Optimize GenAI costs through model selection, caching, and batching strategies
4. **Regulatory Compliance**: Maintain DPDP Act compliance with data anonymization and audit trails
5. **High Availability**: Ensure 99.9% uptime through fallback mechanisms and circuit breakers
6. **Cultural Sensitivity**: Provide culturally appropriate responses adapted to Indian context

### Key Design Decisions

**Model Selection Strategy**: Use Claude 3 Haiku for fast, cost-effective tasks (intent classification, simple queries) and Claude 3.5 Sonnet for complex reasoning (dispute resolution, document analysis). This dual-model approach optimizes the cost-performance tradeoff.

**Data Privacy Architecture**: Implement anonymization layer before all Bedrock API calls to ensure PII never leaves the TrustGraph system. All data processing occurs in ap-south-1 region for DPDP Act compliance.

**Prompt Caching**: Leverage AWS Bedrock's prompt caching feature to reduce costs by up to 90% and latency by up to 85% for repeated prompts with common prefixes (system instructions, tool definitions).

**Fallback Strategy**: Maintain rule-based alternatives for all GenAI features to ensure service continuity when Bedrock is unavailable or rate-limited.

**Multilingual Support**: Use Claude's native multilingual capabilities combined with Bhashini API for 22 Indian constitutional languages, handling code-mixing and regional dialects.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TrustGraph Engine                         │
│                     (ap-south-1 Region)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bedrock Integration Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Anonymization│  │ Model Router │  │ Cache Manager│          │
│  │   Service    │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Intent          │  │  Dispute         │  │  Document        │
│  Classifier      │  │  Resolver        │  │  Analyzer        │
│  (Haiku)         │  │  (Sonnet)        │  │  (Sonnet+Vision) │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Voice Guidance  │  │  Fraud Detector  │  │  Embeddings      │
│  (Haiku)         │  │  (Sonnet+Titan)  │  │  (Titan)         │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Bedrock Service                           │
│                     (ap-south-1 Region)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Claude 3     │  │ Claude 3.5   │  │ Titan Text   │          │
│  │ Haiku        │  │ Sonnet       │  │ Embeddings V2│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audit & Monitoring Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Blockchain   │  │ CloudWatch   │  │ Cost         │          │
│  │ Audit Trail  │  │ Metrics      │  │ Tracking     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

The Bedrock integration consists of six primary components:

1. **Anonymization Service**: Removes PII before sending data to Bedrock
2. **Model Router**: Selects optimal model based on task complexity and cost
3. **Cache Manager**: Implements prompt caching and response caching strategies
4. **Intent Classifier**: Processes voice commands using Claude Haiku
5. **Dispute Resolver**: Analyzes conflicts using Claude Sonnet
6. **Document Analyzer**: Extracts certificate data using Claude Sonnet with vision
7. **Fraud Detector**: Identifies suspicious patterns using Claude Sonnet and Titan Embeddings
8. **Voice Guidance Generator**: Creates personalized responses using Claude Haiku

### Regional Architecture

All components operate exclusively in the ap-south-1 (Mumbai) region to comply with DPDP Act data residency requirements:

```
ap-south-1 (Mumbai) - Primary Region
├── Lambda Functions (Python 3.11)
├── AWS Bedrock (Claude + Titan models)
├── Amazon Neptune (Trust graph database)
├── Amazon S3 (Encrypted credential storage)
├── AWS KMS (Cryptographic keys)
└── Amazon Managed Blockchain (Audit trail)
```

**Note**: AWS Bedrock is available in ap-south-1 region. If specific models are not available, we will use Cross-Region Inference (CRIS) with data residency controls to ensure Indian data stays in India while accessing models from nearby regions.


## Components and Interfaces

### 1. Anonymization Service

**Purpose**: Remove PII from data before sending to Bedrock to ensure DPDP Act compliance.

**Interface**:
```python
class AnonymizationService:
    async def anonymize_text(
        self, 
        text: str, 
        context: Dict[str, Any]
    ) -> AnonymizedData:
        """
        Remove PII from text while preserving semantic meaning.
        
        Args:
            text: Input text containing potential PII
            context: Additional context (user_id, language, etc.)
            
        Returns:
            AnonymizedData with original_text, anonymized_text, 
            and mapping for de-anonymization
        """
        pass
    
    async def de_anonymize_response(
        self, 
        response: str, 
        mapping: Dict[str, str]
    ) -> str:
        """
        Restore specific identifiers in Bedrock response if needed.
        
        Args:
            response: Bedrock model response
            mapping: Anonymization mapping from anonymize_text
            
        Returns:
            Response with restored identifiers where appropriate
        """
        pass
```

**Anonymization Rules**:
- Aadhaar numbers → `[AADHAAR_ID]`
- Phone numbers → `[PHONE]`
- Names → `[WORKER_NAME]`, `[EMPLOYER_NAME]`
- Addresses → `[LOCATION]`
- Bank account numbers → `[ACCOUNT]`
- Preserve: Work type, skills, dates, amounts (for context)

### 2. Model Router

**Purpose**: Select optimal Bedrock model based on task complexity, latency requirements, and cost.

**Interface**:
```python
class ModelRouter:
    async def route_request(
        self, 
        task_type: TaskType, 
        complexity_score: float,
        latency_requirement: int  # milliseconds
    ) -> ModelConfig:
        """
        Determine which Bedrock model to use for a request.
        
        Args:
            task_type: Type of task (INTENT, DISPUTE, DOCUMENT, etc.)
            complexity_score: 0-1 score indicating task complexity
            latency_requirement: Maximum acceptable latency in ms
            
        Returns:
            ModelConfig with model_id, parameters, and fallback options
        """
        pass
```

**Routing Logic**:
```python
# Intent Classification
if task_type == TaskType.INTENT_CLASSIFICATION:
    if latency_requirement < 500:
        return ModelConfig(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            max_tokens=100,
            temperature=0.3
        )

# Dispute Resolution
elif task_type == TaskType.DISPUTE_RESOLUTION:
    return ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=2000,
        temperature=0.7
    )

# Document Analysis
elif task_type == TaskType.DOCUMENT_ANALYSIS:
    return ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=1500,
        temperature=0.2,
        supports_vision=True
    )
```

### 3. Cache Manager

**Purpose**: Implement prompt caching and response caching to reduce costs and latency.

**Interface**:
```python
class CacheManager:
    async def get_cached_response(
        self, 
        cache_key: str
    ) -> Optional[CachedResponse]:
        """Check if response exists in cache."""
        pass
    
    async def cache_response(
        self, 
        cache_key: str, 
        response: str,
        ttl: int = 300  # 5 minutes default
    ) -> None:
        """Store response in cache with TTL."""
        pass
    
    def build_prompt_with_cache_points(
        self, 
        system_prompt: str,
        user_message: str,
        cache_system: bool = True
    ) -> List[Dict]:
        """
        Build prompt with Bedrock cache points.
        
        Returns messages list with cachePoint markers for Bedrock.
        """
        pass
```

**Caching Strategy**:
1. **Prompt Caching**: Cache system prompts and tool definitions (90% cost reduction)
2. **Response Caching**: Cache responses for identical queries (100% cost reduction)
3. **Semantic Caching**: Use Titan Embeddings to find similar queries (40% cost reduction)


### 4. Intent Classifier

**Purpose**: Understand user voice commands in regional languages with dialects and code-mixing.

**Interface**:
```python
class IntentClassifier:
    async def classify_intent(
        self, 
        transcribed_text: str,
        language: str,
        user_context: UserContext
    ) -> IntentResult:
        """
        Classify user intent from voice command.
        
        Args:
            transcribed_text: Text from Bhashini/Transcribe
            language: ISO language code (hi, ta, te, etc.)
            user_context: User's history, preferences, literacy level
            
        Returns:
            IntentResult with intent, confidence, entities, and clarification
        """
        pass
```

**Supported Intents**:
- `CHECK_TRUST_SCORE`: View current trust score
- `ADD_WORK_RECORD`: Add new work completion
- `REQUEST_PAYMENT`: Request payment from employer
- `VERIFY_CREDENTIAL`: Verify skill certificate
- `RAISE_DISPUTE`: Report payment or work quality issue
- `GET_HELP`: Request guidance or support
- `UPDATE_PROFILE`: Modify personal information

**Implementation**:
```python
async def classify_intent(self, transcribed_text, language, user_context):
    # Anonymize input
    anonymized = await self.anonymization_service.anonymize_text(
        transcribed_text, 
        {"user_id": user_context.user_id, "language": language}
    )
    
    # Build prompt with caching
    messages = self.cache_manager.build_prompt_with_cache_points(
        system_prompt=self._get_intent_system_prompt(language),
        user_message=anonymized.text,
        cache_system=True
    )
    
    # Call Bedrock with Haiku
    response = await self.bedrock_client.invoke_model(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        messages=messages,
        max_tokens=100,
        temperature=0.3
    )
    
    # Parse intent from response
    intent_data = json.loads(response["content"][0]["text"])
    
    return IntentResult(
        intent=intent_data["intent"],
        confidence=intent_data["confidence"],
        entities=intent_data["entities"],
        needs_clarification=intent_data["confidence"] < 0.8
    )
```

### 5. Dispute Resolver

**Purpose**: Analyze worker-employer disputes and suggest fair resolutions based on Indian labor laws and regional context.

**Interface**:
```python
class DisputeResolver:
    async def analyze_dispute(
        self, 
        dispute: DisputeData
    ) -> DisputeResolution:
        """
        Analyze dispute and generate resolution suggestions.
        
        Args:
            dispute: Dispute details including parties, work history, 
                    payments, communications, and dispute type
            
        Returns:
            DisputeResolution with analysis, suggested resolutions,
            reasoning, and escalation recommendation
        """
        pass
```

**Dispute Types**:
- `PAYMENT_DELAY`: Employer delayed payment beyond agreed terms
- `PAYMENT_AMOUNT`: Disagreement on payment amount
- `WORK_QUALITY`: Employer claims poor work quality
- `SCOPE_CREEP`: Work scope exceeded original agreement
- `SAFETY_ISSUE`: Unsafe working conditions
- `HARASSMENT`: Workplace harassment or discrimination

**Implementation**:
```python
async def analyze_dispute(self, dispute: DisputeData):
    # Anonymize dispute data
    anonymized_dispute = await self.anonymization_service.anonymize_dispute(
        dispute
    )
    
    # Build context-rich prompt
    prompt = self._build_dispute_prompt(
        dispute_type=dispute.type,
        work_history=anonymized_dispute.work_history,
        payment_records=anonymized_dispute.payments,
        communications=anonymized_dispute.messages,
        regional_context=dispute.location,
        labor_laws=self._get_applicable_laws(dispute.location)
    )
    
    # Call Bedrock with Sonnet for complex reasoning
    response = await self.bedrock_client.invoke_model(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=prompt,
        max_tokens=2000,
        temperature=0.7
    )
    
    # Parse resolution suggestions
    resolution_data = json.loads(response["content"][0]["text"])
    
    return DisputeResolution(
        analysis=resolution_data["analysis"],
        suggested_resolutions=resolution_data["resolutions"],
        reasoning=resolution_data["reasoning"],
        requires_human_review=resolution_data["complexity_score"] > 0.8
    )
```


### 6. Document Analyzer

**Purpose**: Extract and verify information from skill certificates using vision capabilities.

**Interface**:
```python
class DocumentAnalyzer:
    async def analyze_certificate(
        self, 
        image_data: bytes,
        certificate_type: CertificateType
    ) -> CertificateAnalysis:
        """
        Extract structured data from certificate image.
        
        Args:
            image_data: Certificate image bytes (JPEG/PNG)
            certificate_type: Type of certificate (NSDC, PMKVY, ITI, etc.)
            
        Returns:
            CertificateAnalysis with extracted fields, confidence scores,
            and verification status
        """
        pass
```

**Supported Certificate Types**:
- `NSDC`: National Skill Development Corporation certificates
- `PMKVY`: Pradhan Mantri Kaushal Vikas Yojana certificates
- `ITI`: Industrial Training Institute certificates
- `STATE_SKILL`: State-level skill development certificates
- `PRIVATE_TRAINING`: Private training institute certificates

**Implementation**:
```python
async def analyze_certificate(self, image_data, certificate_type):
    # Encode image to base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Build vision prompt
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": self._get_certificate_extraction_prompt(
                        certificate_type
                    )
                }
            ]
        }
    ]
    
    # Call Bedrock with Sonnet + Vision
    response = await self.bedrock_client.invoke_model(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=messages,
        max_tokens=1500,
        temperature=0.2
    )
    
    # Parse extracted data
    extracted = json.loads(response["content"][0]["text"])
    
    # Validate against known patterns
    validation = self._validate_certificate_data(
        extracted, 
        certificate_type
    )
    
    return CertificateAnalysis(
        certificate_number=extracted["certificate_number"],
        issuing_authority=extracted["issuing_authority"],
        skill_name=extracted["skill_name"],
        issue_date=extracted["issue_date"],
        validity_period=extracted["validity_period"],
        confidence_scores=extracted["confidence"],
        requires_manual_review=validation.confidence < 0.85
    )
```

### 7. Fraud Detector

**Purpose**: Identify suspicious patterns in credentials and work history using text analysis and embeddings.

**Interface**:
```python
class FraudDetector:
    async def analyze_credential(
        self, 
        credential_data: CredentialData
    ) -> FraudAnalysis:
        """
        Analyze credential for fraud indicators.
        
        Args:
            credential_data: Work record, reviews, and metadata
            
        Returns:
            FraudAnalysis with risk score, indicators, and reasoning
        """
        pass
    
    async def find_similar_content(
        self, 
        text: str,
        threshold: float = 0.85
    ) -> List[SimilarContent]:
        """
        Find semantically similar content using Titan Embeddings.
        
        Args:
            text: Text to search for (work description, review, etc.)
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar content with similarity scores
        """
        pass
```

**Fraud Indicators**:
- Duplicate or copied work descriptions
- Unrealistic work completion times
- Coordinated fake reviews (similar language patterns)
- Inconsistent skill progression
- Suspicious certificate patterns
- Geographic impossibilities (work in multiple locations simultaneously)

**Implementation**:
```python
async def analyze_credential(self, credential_data):
    # Anonymize credential data
    anonymized = await self.anonymization_service.anonymize_credential(
        credential_data
    )
    
    # Check for duplicate content using embeddings
    work_desc_embedding = await self._get_embedding(
        anonymized.work_description
    )
    similar_content = await self._search_similar_embeddings(
        work_desc_embedding,
        threshold=0.85
    )
    
    # Analyze text patterns with Sonnet
    prompt = self._build_fraud_analysis_prompt(
        work_description=anonymized.work_description,
        reviews=anonymized.reviews,
        work_history=anonymized.history,
        similar_content_count=len(similar_content)
    )
    
    response = await self.bedrock_client.invoke_model(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=prompt,
        max_tokens=1000,
        temperature=0.2
    )
    
    analysis = json.loads(response["content"][0]["text"])
    
    return FraudAnalysis(
        risk_score=analysis["risk_score"],  # 0-100
        indicators=analysis["fraud_indicators"],
        reasoning=analysis["reasoning"],
        requires_review=analysis["risk_score"] > 70,
        similar_content_found=len(similar_content) > 0
    )
```


### 8. Voice Guidance Generator

**Purpose**: Generate personalized, culturally appropriate voice responses adapted to user's literacy level.

**Interface**:
```python
class VoiceGuidanceGenerator:
    async def generate_guidance(
        self, 
        query: str,
        user_context: UserContext,
        conversation_history: List[Message]
    ) -> GuidanceResponse:
        """
        Generate personalized voice guidance.
        
        Args:
            query: User's question or request
            user_context: User profile with literacy level, language, occupation
            conversation_history: Recent conversation for context
            
        Returns:
            GuidanceResponse with text, audio_url, and follow_up_suggestions
        """
        pass
```

**Literacy Level Adaptation**:
```python
# Low literacy (simple language, step-by-step)
"आपका काम पूरा हो गया है। अब पैसे मांगने के लिए यह करें:
1. फोन पर बोलें 'पैसे चाहिए'
2. अपने मालिक का नाम बोलें
3. काम की तारीख बोलें
बस, हो गया!"

# Medium literacy (more detail, some technical terms)
"आपका काम रिकॉर्ड सिस्टम में दर्ज हो गया है। पेमेंट रिक्वेस्ट भेजने के लिए:
1. वॉइस कमांड दें: 'पेमेंट रिक्वेस्ट भेजें'
2. एम्प्लॉयर का नाम और काम की डिटेल्स बताएं
3. सिस्टम आपकी रिक्वेस्ट एम्प्लॉयर को भेज देगा"

# High literacy (detailed, technical)
"Your work record has been successfully logged in the TrustGraph system. 
To initiate a payment request:
1. Use voice command: 'Request payment from [employer name]'
2. The system will retrieve your verified work record
3. Payment request will be sent via UPI with blockchain verification
4. You'll receive notification when employer approves"
```

**Implementation**:
```python
async def generate_guidance(self, query, user_context, conversation_history):
    # Anonymize query
    anonymized_query = await self.anonymization_service.anonymize_text(
        query,
        {"user_id": user_context.user_id}
    )
    
    # Build context-aware prompt
    messages = self.cache_manager.build_prompt_with_cache_points(
        system_prompt=self._get_guidance_system_prompt(
            literacy_level=user_context.literacy_level,
            language=user_context.language,
            occupation=user_context.occupation,
            cultural_context=user_context.region
        ),
        user_message=anonymized_query.text,
        cache_system=True
    )
    
    # Add conversation history for context
    for msg in conversation_history[-5:]:  # Last 5 turns
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Call Bedrock with Haiku
    response = await self.bedrock_client.invoke_model(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        messages=messages,
        max_tokens=500,
        temperature=0.7
    )
    
    guidance_text = response["content"][0]["text"]
    
    # Generate audio using Bhashini/Polly
    audio_url = await self.voice_service.text_to_speech(
        guidance_text,
        language=user_context.language
    )
    
    return GuidanceResponse(
        text=guidance_text,
        audio_url=audio_url,
        follow_up_suggestions=self._generate_follow_ups(
            query, 
            user_context
        )
    )
```

## Data Models

### AnonymizedData
```python
@dataclass
class AnonymizedData:
    original_text: str
    anonymized_text: str
    mapping: Dict[str, str]  # PII type -> placeholder
    language: str
    timestamp: datetime
```

### IntentResult
```python
@dataclass
class IntentResult:
    intent: str  # Intent name
    confidence: float  # 0-1
    entities: Dict[str, Any]  # Extracted entities
    needs_clarification: bool
    clarification_question: Optional[str]
```

### DisputeResolution
```python
@dataclass
class DisputeResolution:
    analysis: str  # Detailed analysis of dispute
    suggested_resolutions: List[Resolution]
    reasoning: str  # Explanation of suggestions
    requires_human_review: bool
    estimated_resolution_time: int  # days
    applicable_laws: List[str]  # Relevant labor laws
```

### Resolution
```python
@dataclass
class Resolution:
    title: str
    description: str
    steps: List[str]
    pros: List[str]
    cons: List[str]
    fairness_score: float  # 0-1
```

### CertificateAnalysis
```python
@dataclass
class CertificateAnalysis:
    certificate_number: str
    issuing_authority: str
    skill_name: str
    issue_date: date
    validity_period: Optional[date]
    confidence_scores: Dict[str, float]  # Field -> confidence
    requires_manual_review: bool
    verification_status: str  # VERIFIED, PENDING, FAILED
```

### FraudAnalysis
```python
@dataclass
class FraudAnalysis:
    risk_score: int  # 0-100
    indicators: List[FraudIndicator]
    reasoning: str
    requires_review: bool
    similar_content_found: bool
    recommended_action: str  # APPROVE, REVIEW, REJECT
```

### FraudIndicator
```python
@dataclass
class FraudIndicator:
    type: str  # DUPLICATE_CONTENT, UNREALISTIC_TIMELINE, etc.
    severity: str  # LOW, MEDIUM, HIGH
    description: str
    evidence: str
```

