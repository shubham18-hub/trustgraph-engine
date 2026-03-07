"""
AWS Bedrock Service - Real GenAI Integration
Implements Claude 3 Haiku for Hindi voice intent classification
"""

import boto3
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class BedrockService:
    """AWS Bedrock integration for TrustGraph Engine"""
    
    def __init__(self, region: str = "ap-south-1"):
        """Initialize Bedrock client"""
        self.region = region
        try:
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=region
            )
            self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            logger.info(f"Bedrock client initialized in {region}")
        except Exception as e:
            logger.warning(f"Bedrock client initialization failed: {e}")
            self.bedrock = None
    
    async def classify_intent(self, text: str, language: str = "hi") -> Dict:
        """
        Classify user intent using Claude 3 Haiku
        
        Args:
            text: User's voice command (transcribed)
            language: Language code (hi, en, etc.)
            
        Returns:
            Intent classification result
        """
        if not self.bedrock:
            return self._fallback_intent_classification(text, language)
        
        try:
            start_time = datetime.now()
            
            # Build prompt for Claude
            prompt = self._build_intent_prompt(text, language)
            
            # Call Bedrock API
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 150,
                    "temperature": 0.3,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Extract JSON from response
            try:
                intent_data = json.loads(content)
            except:
                # If response isn't pure JSON, try to extract it
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    intent_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse intent from response")
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "intent": intent_data.get("intent", "UNKNOWN"),
                "confidence": intent_data.get("confidence", 0.0),
                "entities": intent_data.get("entities", {}),
                "reasoning": intent_data.get("reasoning", ""),
                "needs_clarification": intent_data.get("confidence", 0.0) < 0.8,
                "latency_ms": latency_ms,
                "model": self.model_id,
                "language": language,
                "source": "bedrock"
            }
            
            logger.info(f"Intent classified: {result['intent']} (confidence: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Bedrock intent classification failed: {e}")
            return self._fallback_intent_classification(text, language)
    
    def _build_intent_prompt(self, text: str, language: str) -> str:
        """Build prompt for Claude with Indian worker context"""
        
        language_names = {
            "hi": "Hindi",
            "en": "English",
            "bn": "Bengali",
            "te": "Telugu",
            "mr": "Marathi",
            "ta": "Tamil"
        }
        
        lang_name = language_names.get(language, "Hindi")
        
        return f"""You are an AI assistant for TrustGraph, a platform helping India's 490 million informal workers.

Your task: Classify the user's intent from their voice command in {lang_name}.

User's command: "{text}"

Available intents:
1. CHECK_TRUST_SCORE - User wants to know their trust/credit score
   Examples: "मेरा ट्रस्ट स्कोर क्या है?", "what is my score?", "score check karo"

2. ADD_WORK_RECORD - User completed work and wants to record it
   Examples: "काम पूरा हो गया", "work completed", "kaam khatam hua"

3. REQUEST_PAYMENT - User wants to request payment from employer
   Examples: "पैसे चाहिए", "payment chahiye", "when will I get paid?"

4. VERIFY_CREDENTIAL - User wants to verify or show their work certificate
   Examples: "प्रमाणपत्र दिखाओ", "show certificate", "credential verify karo"

5. RAISE_DISPUTE - User has a problem with payment or work
   Examples: "पैसे नहीं मिले", "payment not received", "problem hai"

6. GET_HELP - User needs help or doesn't understand
   Examples: "मदद चाहिए", "help", "samajh nahi aaya"

Context:
- Users are informal workers (construction, domestic work, delivery, etc.)
- Low digital literacy, prefer voice commands
- May use code-mixing (Hindi + English)
- May have regional dialects

Respond ONLY with valid JSON in this exact format:
{{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "entities": {{}},
  "reasoning": "brief explanation"
}}

Be confident if the intent is clear. Use confidence < 0.8 if ambiguous."""

    def _fallback_intent_classification(self, text: str, language: str) -> Dict:
        """Fallback rule-based intent classification when Bedrock unavailable"""
        
        text_lower = text.lower()
        
        # Simple keyword matching
        if any(word in text_lower for word in ["score", "स्कोर", "rating", "रेटिंग"]):
            intent = "CHECK_TRUST_SCORE"
            confidence = 0.85
        elif any(word in text_lower for word in ["complete", "पूरा", "finish", "खत्म", "done"]):
            intent = "ADD_WORK_RECORD"
            confidence = 0.80
        elif any(word in text_lower for word in ["payment", "पैसे", "money", "भुगतान", "paid"]):
            intent = "REQUEST_PAYMENT"
            confidence = 0.85
        elif any(word in text_lower for word in ["certificate", "प्रमाणपत्र", "credential", "verify"]):
            intent = "VERIFY_CREDENTIAL"
            confidence = 0.80
        elif any(word in text_lower for word in ["problem", "समस्या", "issue", "dispute", "not received"]):
            intent = "RAISE_DISPUTE"
            confidence = 0.75
        elif any(word in text_lower for word in ["help", "मदद", "support", "सहायता"]):
            intent = "GET_HELP"
            confidence = 0.90
        else:
            intent = "UNKNOWN"
            confidence = 0.50
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": {},
            "reasoning": "Fallback rule-based classification",
            "needs_clarification": confidence < 0.8,
            "latency_ms": 10,
            "model": "rule-based",
            "language": language,
            "source": "fallback"
        }

# Initialize service
bedrock_service = BedrockService()
