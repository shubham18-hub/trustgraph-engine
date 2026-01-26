"""
Voice Service for TrustGraph Engine
Integrates Bhashini API with AWS Transcribe/Polly for 22 Indian languages
Implements voice-first interaction for milestone logging and user guidance
"""

import json
import boto3
import base64
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import uuid
import os
from dataclasses import dataclass, asdict
import re
from enum import Enum

logger = logging.getLogger(__name__)

class VoiceIntent(Enum):
    """Supported voice intents for TrustGraph operations"""
    MILESTONE_COMPLETION = "milestone_completion"
    PAYMENT_INQUIRY = "payment_inquiry" 
    WORK_REGISTRATION = "work_registration"
    SKILL_VERIFICATION = "skill_verification"
    HELP_REQUEST = "help_request"
    CREDENTIAL_SHARE = "credential_share"
    TRUST_SCORE_CHECK = "trust_score_check"
    UNKNOWN = "unknown"

@dataclass
class VoiceProcessingResult:
    """Result of voice processing operation"""
    transcribed_text: str
    detected_language: str
    intent: VoiceIntent
    entities: Dict[str, Any]
    confidence: float
    response_text: str
    response_audio_url: str
    processing_time_ms: int
    fallback_used: bool
    session_id: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['intent'] = self.intent.value
        return result

class BhashiniAPIClient:
    """Client for Bhashini API integration with fallback mechanisms"""
    
    def __init__(self):
        self.api_key = os.environ.get('BHASHINI_API_KEY')
        self.base_url = os.environ.get('BHASHINI_BASE_URL', 'https://bhashini.gov.in/api/v1')
        self.timeout = int(os.environ.get('BHASHINI_TIMEOUT', '10'))
        
        # Supported languages mapping
        self.supported_languages = {
            'hi': 'Hindi', 'bn': 'Bengali', 'te': 'Telugu', 'mr': 'Marathi',
            'ta': 'Tamil', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam',
            'or': 'Odia', 'pa': 'Punjabi', 'as': 'Assamese', 'ur': 'Urdu',
            'ne': 'Nepali', 'ks': 'Kashmiri', 'sd': 'Sindhi', 'mai': 'Maithili',
            'bho': 'Bhojpuri', 'gom': 'Konkani', 'mni': 'Manipuri', 
            'sat': 'Santali', 'doi': 'Dogri', 'brx': 'Bodo'
        }
        
    async def transcribe_audio(self, audio_data: bytes, source_language: str) -> Dict[str, Any]:
        """
        Transcribe audio using Bhashini ASR service
        
        Args:
            audio_data: Raw audio bytes (WAV format preferred)
            source_language: ISO 639-1 language code
            
        Returns:
            Dict with transcription result and metadata
        """
        try:
            # Validate language support
            if source_language not in self.supported_languages:
                logger.warning(f"Language {source_language} not supported, defaulting to Hindi")
                source_language = 'hi'
            
            # Prepare request payload
            payload = {
                'audio': base64.b64encode(audio_data).decode('utf-8'),
                'language': source_language,
                'format': 'wav',
                'sample_rate': 16000,
                'encoding': 'LINEAR16',
                'model': 'latest'  # Use latest ASR model
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'TrustGraph-Engine/1.0'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/asr/transcribe',
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'transcription': result.get('transcription', ''),
                            'confidence': float(result.get('confidence', 0.0)),
                            'detected_language': result.get('detected_language', source_language),
                            'processing_time': result.get('processing_time_ms', 0),
                            'alternatives': result.get('alternatives', [])
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Bhashini ASR failed: {response.status} - {error_text}")
                        return {
                            'success': False, 
                            'error': f'Bhashini ASR error: {response.status}',
                            'error_details': error_text
                        }
                        
        except asyncio.TimeoutError:
            logger.error("Bhashini ASR request timeout")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Bhashini ASR error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def translate_text(self, text: str, source_lang: str, target_lang: str = 'en') -> Dict[str, Any]:
        """
        Translate text using Bhashini NMT service
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with translation result
        """
        try:
            payload = {
                'text': text,
                'source_language': source_lang,
                'target_language': target_lang,
                'model': 'latest'
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/nmt/translate',
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'translated_text': result.get('translated_text', ''),
                            'confidence': float(result.get('confidence', 0.0)),
                            'source_language': source_lang,
                            'target_language': target_lang
                        }
                    else:
                        return {'success': False, 'error': f'Translation failed: {response.status}'}
                        
        except Exception as e:
            logger.error(f"Bhashini translation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def synthesize_speech(self, text: str, target_language: str, voice_type: str = 'female') -> Dict[str, Any]:
        """
        Generate speech using Bhashini TTS service
        
        Args:
            text: Text to synthesize
            target_language: Target language for speech
            voice_type: Voice type (male/female)
            
        Returns:
            Dict with audio generation result
        """
        try:
            payload = {
                'text': text,
                'language': target_language,
                'voice': voice_type,
                'format': 'wav',
                'sample_rate': 22050,
                'speed': 1.0,
                'pitch': 1.0
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/tts/synthesize',
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'audio_data': result.get('audio_data', ''),
                            'audio_url': result.get('audio_url', ''),
                            'duration': result.get('duration_seconds', 0),
                            'format': 'wav'
                        }
                    else:
                        return {'success': False, 'error': f'TTS failed: {response.status}'}
                        
        except Exception as e:
            logger.error(f"Bhashini TTS error: {str(e)}")
            return {'success': False, 'error': str(e)}

class AWSVoiceServices:
    """AWS voice services for fallback when Bhashini is unavailable"""
    
    def __init__(self):
        self.transcribe_client = boto3.client('transcribe', region_name='ap-south-1')
        self.polly_client = boto3.client('polly', region_name='ap-south-1')
        self.s3_client = boto3.client('s3', region_name='ap-south-1')
        self.bucket_name = os.environ.get('VOICE_ASSETS_BUCKET', 'trustgraph-voice-assets')
        
        # Language mapping for AWS services
        self.aws_language_map = {
            'hi': 'hi-IN', 'bn': 'bn-IN', 'te': 'te-IN', 'mr': 'mr-IN',
            'ta': 'ta-IN', 'gu': 'gu-IN', 'kn': 'kn-IN', 'ml': 'ml-IN',
            'or': 'or-IN', 'pa': 'pa-IN', 'as': 'as-IN', 'ur': 'ur-IN',
            'en': 'en-IN'
        }
        
        # Polly voice mapping
        self.polly_voices = {
            'hi': {'neural': 'Kajal', 'standard': 'Aditi'},
            'en': {'neural': 'Joanna', 'standard': 'Joanna'},
            'te': {'neural': 'Kajal', 'standard': 'Aditi'},  # Fallback to Hindi
            'ta': {'neural': 'Kajal', 'standard': 'Aditi'},  # Fallback to Hindi
        }
    
    async def transcribe_audio_fallback(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """
        Fallback transcription using AWS Transcribe
        
        Args:
            audio_data: Raw audio bytes
            language: Language code
            
        Returns:
            Dict with transcription result
        """
        try:
            # Upload audio to S3 for Transcribe processing
            audio_key = f"transcribe-input/{uuid.uuid4()}.wav"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=audio_key,
                Body=audio_data,
                ContentType='audio/wav',
                ServerSideEncryption='AES256'
            )
            
            # Map language for AWS Transcribe
            transcribe_language = self.aws_language_map.get(language, 'hi-IN')
            job_name = f"trustgraph-transcribe-{uuid.uuid4()}"
            
            # Start transcription job
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': f's3://{self.bucket_name}/{audio_key}'},
                MediaFormat='wav',
                LanguageCode=transcribe_language,
                Settings={
                    'ShowSpeakerLabels': False,
                    'MaxSpeakerLabels': 1,
                    'ShowAlternatives': True,
                    'MaxAlternatives': 3
                }
            )
            
            # Poll for completion (with timeout)
            max_wait = 30  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    
                    # Download and parse transcript
                    import urllib.request
                    with urllib.request.urlopen(transcript_uri) as response:
                        transcript_data = json.loads(response.read().decode())
                    
                    transcription = transcript_data['results']['transcripts'][0]['transcript']
                    
                    # Extract confidence from items
                    items = transcript_data['results'].get('items', [])
                    confidences = [
                        float(item.get('alternatives', [{}])[0].get('confidence', 0.0))
                        for item in items if item.get('type') == 'pronunciation'
                    ]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    # Cleanup S3 object
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=audio_key)
                    
                    return {
                        'success': True,
                        'transcription': transcription,
                        'confidence': avg_confidence,
                        'detected_language': language,
                        'alternatives': transcript_data['results'].get('alternatives', [])
                    }
                    
                elif status == 'FAILED':
                    failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    return {'success': False, 'error': f'Transcription failed: {failure_reason}'}
                
                await asyncio.sleep(2)
                wait_time += 2
            
            return {'success': False, 'error': 'Transcription timeout'}
            
        except Exception as e:
            logger.error(f"AWS Transcribe fallback error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def synthesize_speech_fallback(self, text: str, language: str, voice_type: str = 'neural') -> Dict[str, Any]:
        """
        Fallback TTS using Amazon Polly
        
        Args:
            text: Text to synthesize
            language: Target language
            voice_type: Voice type (neural/standard)
            
        Returns:
            Dict with audio synthesis result
        """
        try:
            # Get appropriate voice for language
            voice_config = self.polly_voices.get(language, self.polly_voices['hi'])
            voice_id = voice_config.get(voice_type, voice_config['standard'])
            
            # Determine language code for Polly
            language_code = self.aws_language_map.get(language, 'hi-IN')
            engine = 'neural' if voice_type == 'neural' else 'standard'
            
            # Generate speech
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine=engine,
                LanguageCode=language_code,
                TextType='text'
            )
            
            # Upload audio to S3
            audio_key = f"tts-output/{uuid.uuid4()}.mp3"
            audio_stream = response['AudioStream'].read()
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=audio_key,
                Body=audio_stream,
                ContentType='audio/mpeg',
                ServerSideEncryption='AES256'
            )
            
            # Generate presigned URL for audio access
            audio_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': audio_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'success': True,
                'audio_url': audio_url,
                'audio_data': base64.b64encode(audio_stream).decode(),
                'duration': len(text) * 0.1,  # Approximate duration
                'format': 'mp3'
            }
            
        except Exception as e:
            logger.error(f"Polly TTS fallback error: {str(e)}")
            return {'success': False, 'error': str(e)}

class VoiceIntentClassifier:
    """Classify user intents from transcribed text in multiple languages"""
    
    def __init__(self):
        # Intent patterns in multiple languages
        self.intent_patterns = {
            VoiceIntent.MILESTONE_COMPLETION: {
                'hi': ['काम पूरा', 'काम खत्म', 'कार्य समाप्त', 'माइलस्टोन पूरा', 'टास्क कम्प्लीट'],
                'en': ['work complete', 'task done', 'milestone complete', 'finished work', 'job done'],
                'te': ['పని పూర్తి', 'కార్యం ముగిసింది'],
                'ta': ['வேலை முடிந்தது', 'பணி நிறைவு'],
                'bn': ['কাজ শেষ', 'কার্য সম্পন্ন']
            },
            VoiceIntent.PAYMENT_INQUIRY: {
                'hi': ['पैसा कब', 'भुगतान कब', 'पेमेंट स्टेटस', 'सैलरी कब', 'रुपया कब मिलेगा'],
                'en': ['payment when', 'money receive', 'salary when', 'payment status', 'when money'],
                'te': ['డబ్బు ఎప్పుడు', 'చెల్లింపు ఎప్పుడు'],
                'ta': ['பணம் எப்போது', 'சம்பளம் எப்போது'],
                'bn': ['টাকা কবে', 'বেতন কবে']
            },
            VoiceIntent.WORK_REGISTRATION: {
                'hi': ['नया काम', 'काम रजिस्टर', 'कार्य पंजीकरण', 'जॉब एंट्री', 'वर्क एंट्री'],
                'en': ['new work', 'register work', 'job entry', 'work registration', 'add work'],
                'te': ['కొత్त పని', 'పని నమోదు'],
                'ta': ['புதிய வேலை', 'வேலை பதிவு'],
                'bn': ['নতুন কাজ', 'কাজ নিবন্ধন']
            },
            VoiceIntent.SKILL_VERIFICATION: {
                'hi': ['हुनर सत्यापन', 'स्किल वेरिफाई', 'प्रमाणपत्र', 'योग्यता प्रमाण', 'सर्टिफिकेट'],
                'en': ['skill verify', 'certificate', 'skill certificate', 'verify skills', 'qualification'],
                'te': ['నైపుణ్యం ధృవీకరణ', 'సర్టిఫికేట్'],
                'ta': ['திறமை சரிபார்ப்பு', 'சான்றிதழ்'],
                'bn': ['দক্ষতা যাচাই', 'সার্টিফিকেট']
            },
            VoiceIntent.TRUST_SCORE_CHECK: {
                'hi': ['ट्रस्ट स्कोर', 'क्रेडिट स्कोर', 'मेरा स्कोर', 'विश्वसनीयता स्कोर'],
                'en': ['trust score', 'credit score', 'my score', 'reliability score'],
                'te': ['ట్రస్ట్ స్కోర్', 'క్రెడిట్ స్కోర్'],
                'ta': ['நம்பிக்கை மதிப்பெண்', 'கடன் மதிப்பெண்'],
                'bn': ['বিশ্বাস স্কোর', 'ক্রেডিট স্কোর']
            },
            VoiceIntent.HELP_REQUEST: {
                'hi': ['मदद', 'सहायता', 'हेल्प', 'मार्गदर्शन', 'कैसे करें'],
                'en': ['help', 'assistance', 'guide', 'how to', 'support'],
                'te': ['సహాయం', 'మార్గదర్శకత్వం'],
                'ta': ['உதவி', 'வழிகாட்டுதல்'],
                'bn': ['সাহায্য', 'সহায়তা']
            }
        }
    
    def classify_intent(self, text: str, language: str = 'hi') -> Tuple[VoiceIntent, float, Dict[str, Any]]:
        """
        Classify intent from transcribed text
        
        Args:
            text: Transcribed text
            language: Detected language
            
        Returns:
            Tuple of (intent, confidence, metadata)
        """
        text_lower = text.lower()
        intent_scores = {}
        
        # Score each intent based on pattern matching
        for intent, lang_patterns in self.intent_patterns.items():
            patterns = lang_patterns.get(language, lang_patterns.get('hi', []))
            
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    score += 1
                    matched_patterns.append(pattern)
            
            if score > 0:
                confidence = min(score / len(patterns), 1.0)
                intent_scores[intent] = {
                    'score': score,
                    'confidence': confidence,
                    'matched_patterns': matched_patterns
                }
        
        if intent_scores:
            best_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]['score'])
            confidence = intent_scores[best_intent]['confidence']
            metadata = intent_scores[best_intent]
        else:
            best_intent = VoiceIntent.UNKNOWN
            confidence = 0.0
            metadata = {}
        
        return best_intent, confidence, metadata
    
    def extract_entities(self, text: str, intent: VoiceIntent, language: str = 'hi') -> Dict[str, Any]:
        """
        Extract entities from text based on intent
        
        Args:
            text: Transcribed text
            intent: Classified intent
            language: Language of text
            
        Returns:
            Dict of extracted entities
        """
        entities = {}
        text_lower = text.lower()
        
        if intent == VoiceIntent.MILESTONE_COMPLETION:
            # Extract work type
            work_types = {
                'hi': ['राजमिस्त्री', 'प्लंबर', 'इलेक्ट्रिशियन', 'पेंटर', 'कारपेंटर'],
                'en': ['mason', 'plumber', 'electrician', 'painter', 'carpenter']
            }
            
            for work_type in work_types.get(language, work_types['hi']):
                if work_type.lower() in text_lower:
                    entities['work_type'] = work_type
                    break
            
            # Extract completion percentage
            percentage_match = re.search(r'(\d+)\s*%', text_lower)
            if percentage_match:
                entities['completion_percentage'] = int(percentage_match.group(1))
        
        elif intent == VoiceIntent.PAYMENT_INQUIRY:
            # Extract amount references
            amount_match = re.search(r'(\d+)\s*(रुपये|rupees|rs)', text_lower)
            if amount_match:
                entities['amount'] = int(amount_match.group(1))
            
            # Extract time references
            time_patterns = ['आज', 'कल', 'today', 'tomorrow', 'yesterday']
            for pattern in time_patterns:
                if pattern.lower() in text_lower:
                    entities['time_reference'] = pattern
                    break
        
        elif intent == VoiceIntent.WORK_REGISTRATION:
            # Extract location
            location_match = re.search(r'(में|at|in)\s+([a-zA-Z\u0900-\u097F\s]+)', text)
            if location_match:
                entities['location'] = location_match.group(2).strip()
        
        return entities

class VoiceResponseGenerator:
    """Generate contextual voice responses in multiple languages"""
    
    def __init__(self):
        self.response_templates = {
            VoiceIntent.MILESTONE_COMPLETION: {
                'hi': {
                    'success': "बहुत अच्छा! आपका {work_type} काम पूरा होने की जानकारी मिली है। कृपया काम की फोटो अपलोड करें और अपने नियोक्ता से पुष्टि कराएं।",
                    'pending': "आपका काम पूरा होने की जानकारी दर्ज की गई है। नियोक्ता की पुष्टि का इंतजार है।",
                    'error': "काम पूरा करने की जानकारी दर्ज करने में समस्या हुई है। कृपया दोबारा कोशिश करें।"
                },
                'en': {
                    'success': "Great! Your {work_type} work completion has been noted. Please upload a photo and get confirmation from your employer.",
                    'pending': "Your work completion has been recorded. Waiting for employer confirmation.",
                    'error': "There was an issue recording your work completion. Please try again."
                }
            },
            VoiceIntent.PAYMENT_INQUIRY: {
                'hi': {
                    'success': "आपका भुगतान स्थिति: {amount} रुपये का भुगतान {status} है। आपको SMS से अपडेट मिलेगा।",
                    'pending': "आपका भुगतान प्रक्रिया में है। 24 घंटे में अपडेट मिलेगा।",
                    'error': "भुगतान की जानकारी लेने में समस्या हुई है। कृपया बाद में कोशिश करें।"
                },
                'en': {
                    'success': "Your payment status: {amount} rupees payment is {status}. You will receive SMS update.",
                    'pending': "Your payment is being processed. Update within 24 hours.",
                    'error': "Unable to fetch payment information. Please try later."
                }
            },
            VoiceIntent.TRUST_SCORE_CHECK: {
                'hi': {
                    'success': "आपका ट्रस्ट स्कोर {score} है। यह {category} श्रेणी में आता है। आपके काम के इतिहास और भुगतान की नियमितता के आधार पर यह स्कोर बना है।",
                    'error': "ट्रस्ट स्कोर की जानकारी लेने में समस्या हुई है।"
                },
                'en': {
                    'success': "Your trust score is {score}. This falls in {category} category. This score is based on your work history and payment consistency.",
                    'error': "Unable to fetch trust score information."
                }
            },
            VoiceIntent.HELP_REQUEST: {
                'hi': {
                    'general': "मैं आपकी सहायता के लिए यहां हूं। आप कह सकते हैं: 'काम पूरा किया', 'पैसा कब मिलेगा', 'नया काम रजिस्टर करना है', या 'मेरा ट्रस्ट स्कोर क्या है'।"
                },
                'en': {
                    'general': "I'm here to help you. You can say: 'work completed', 'when will I get money', 'register new work', or 'what is my trust score'."
                }
            },
            VoiceIntent.UNKNOWN: {
                'hi': {
                    'default': "मुझे समझ नहीं आया। कृपया दोबारा कहें या सहायता के लिए 'मदद' कहें।"
                },
                'en': {
                    'default': "I didn't understand. Please repeat or say 'help' for assistance."
                }
            }
        }
    
    def generate_response(self, intent: VoiceIntent, language: str, 
                         entities: Dict = None, context: Dict = None, 
                         status: str = 'success') -> str:
        """
        Generate contextual response based on intent and context
        
        Args:
            intent: Classified intent
            language: Response language
            entities: Extracted entities
            context: User/session context
            status: Response status (success/pending/error)
            
        Returns:
            Generated response text
        """
        # Get template for intent and language
        intent_templates = self.response_templates.get(intent, self.response_templates[VoiceIntent.UNKNOWN])
        lang_templates = intent_templates.get(language, intent_templates.get('hi', intent_templates.get('en', {})))
        
        # Get specific template based on status
        template = lang_templates.get(status, lang_templates.get('default', ''))
        
        # Format template with entities and context
        if entities:
            try:
                template = template.format(**entities)
            except KeyError:
                # If formatting fails, use template as-is
                pass
        
        # Add personalization if user context available
        if context and context.get('name'):
            name = context['name']
            if language == 'hi':
                template = f"{name} जी, " + template
            else:
                template = f"Hello {name}, " + template
        
        return template

class VoiceService:
    """Main voice service orchestrating all voice operations"""
    
    def __init__(self):
        self.bhashini_client = BhashiniAPIClient()
        self.aws_voice_services = AWSVoiceServices()
        self.intent_classifier = VoiceIntentClassifier()
        self.response_generator = VoiceResponseGenerator()
        
        # Session management
        self.active_sessions = {}
        
    async def process_voice_command(self, audio_data: bytes, user_id: str, 
                                  session_context: Dict = None) -> VoiceProcessingResult:
        """
        Process complete voice command workflow
        
        Args:
            audio_data: Raw audio bytes
            user_id: User identifier
            session_context: Session context and user preferences
            
        Returns:
            VoiceProcessingResult with complete processing information
        """
        start_time = datetime.now()
        session_id = str(uuid.uuid4())
        fallback_used = False
        
        try:
            # Get user language preference
            language = session_context.get('preferred_language', 'hi') if session_context else 'hi'
            
            # Step 1: Transcribe audio (Bhashini primary, AWS fallback)
            logger.info(f"Starting transcription for user {user_id}, language: {language}")
            
            transcription_result = await self.bhashini_client.transcribe_audio(audio_data, language)
            
            if not transcription_result['success']:
                logger.info("Bhashini transcription failed, using AWS fallback")
                transcription_result = await self.aws_voice_services.transcribe_audio_fallback(audio_data, language)
                fallback_used = True
            
            if not transcription_result['success']:
                error_msg = "Transcription failed"
                return VoiceProcessingResult(
                    transcribed_text="",
                    detected_language=language,
                    intent=VoiceIntent.UNKNOWN,
                    entities={},
                    confidence=0.0,
                    response_text=self.response_generator.generate_response(
                        VoiceIntent.UNKNOWN, language, status='error'
                    ),
                    response_audio_url="",
                    processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    fallback_used=fallback_used,
                    session_id=session_id,
                    error=error_msg
                )
            
            transcribed_text = transcription_result['transcription']
            detected_language = transcription_result.get('detected_language', language)
            transcription_confidence = transcription_result.get('confidence', 0.0)
            
            logger.info(f"Transcription successful: '{transcribed_text}' (confidence: {transcription_confidence})")
            
            # Step 2: Classify intent and extract entities
            intent, intent_confidence, intent_metadata = self.intent_classifier.classify_intent(
                transcribed_text, detected_language
            )
            entities = self.intent_classifier.extract_entities(transcribed_text, intent, detected_language)
            
            logger.info(f"Intent classified: {intent.value} (confidence: {intent_confidence})")
            
            # Step 3: Process business logic based on intent
            business_context = await self._process_business_logic(intent, entities, user_id, session_context)
            
            # Step 4: Generate response text
            response_text = self.response_generator.generate_response(
                intent, 
                detected_language, 
                {**entities, **business_context.get('response_data', {})},
                session_context,
                business_context.get('status', 'success')
            )
            
            # Step 5: Generate audio response (Bhashini primary, Polly fallback)
            tts_result = await self.bhashini_client.synthesize_speech(response_text, detected_language)
            
            if not tts_result['success']:
                logger.info("Bhashini TTS failed, using Polly fallback")
                tts_result = await self.aws_voice_services.synthesize_speech_fallback(response_text, detected_language)
                fallback_used = True
            
            response_audio_url = tts_result.get('audio_url', '') if tts_result['success'] else ''
            
            # Calculate overall confidence
            overall_confidence = min(transcription_confidence, intent_confidence)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Store session information
            self.active_sessions[session_id] = {
                'user_id': user_id,
                'intent': intent,
                'entities': entities,
                'context': business_context,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Voice processing completed in {processing_time}ms")
            
            return VoiceProcessingResult(
                transcribed_text=transcribed_text,
                detected_language=detected_language,
                intent=intent,
                entities=entities,
                confidence=overall_confidence,
                response_text=response_text,
                response_audio_url=response_audio_url,
                processing_time_ms=processing_time,
                fallback_used=fallback_used,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Voice processing error for user {user_id}: {str(e)}")
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return VoiceProcessingResult(
                transcribed_text="",
                detected_language=language,
                intent=VoiceIntent.UNKNOWN,
                entities={},
                confidence=0.0,
                response_text=self.response_generator.generate_response(
                    VoiceIntent.UNKNOWN, language, status='error'
                ),
                response_audio_url="",
                processing_time_ms=processing_time,
                fallback_used=fallback_used,
                session_id=session_id,
                error=str(e)
            )
    
    async def _process_business_logic(self, intent: VoiceIntent, entities: Dict, 
                                    user_id: str, context: Dict) -> Dict[str, Any]:
        """
        Process business logic based on classified intent
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            user_id: User identifier
            context: Session context
            
        Returns:
            Dict with business processing results
        """
        try:
            if intent == VoiceIntent.MILESTONE_COMPLETION:
                # TODO: Integrate with milestone service
                return {
                    'status': 'success',
                    'response_data': {
                        'work_type': entities.get('work_type', 'काम')
                    },
                    'action_taken': 'milestone_logged',
                    'next_steps': ['upload_photo', 'employer_confirmation']
                }
            
            elif intent == VoiceIntent.PAYMENT_INQUIRY:
                # TODO: Integrate with payment service
                return {
                    'status': 'success',
                    'response_data': {
                        'amount': '15000',
                        'status': 'प्रक्रिया में'
                    },
                    'action_taken': 'payment_status_checked'
                }
            
            elif intent == VoiceIntent.TRUST_SCORE_CHECK:
                # TODO: Integrate with trust scoring service
                return {
                    'status': 'success',
                    'response_data': {
                        'score': '750',
                        'category': 'अच्छा'
                    },
                    'action_taken': 'trust_score_retrieved'
                }
            
            else:
                return {
                    'status': 'success',
                    'response_data': {},
                    'action_taken': 'information_provided'
                }
                
        except Exception as e:
            logger.error(f"Business logic processing error: {str(e)}")
            return {
                'status': 'error',
                'response_data': {},
                'error': str(e)
            }
    
    def transcribe_audio(self, audio_bytes: bytes, source_language: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for audio transcription
        
        Args:
            audio_bytes: Raw audio data
            source_language: Source language code
            
        Returns:
            Dict with transcription results
        """
        try:
            result = asyncio.run(self.bhashini_client.transcribe_audio(audio_bytes, source_language))
            
            if not result['success']:
                # Fallback to AWS Transcribe
                result = asyncio.run(self.aws_voice_services.transcribe_audio_fallback(audio_bytes, source_language))
            
            return {
                'text': result.get('transcription', ''),
                'confidence': result.get('confidence', 0.0),
                'language': result.get('detected_language', source_language)
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return {
                'text': '',
                'confidence': 0.0,
                'language': source_language,
                'error': str(e)
            }
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for text translation
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with translation results
        """
        try:
            result = asyncio.run(self.bhashini_client.translate_text(text, source_lang, target_lang))
            
            return {
                'translated_text': result.get('translated_text', text),
                'confidence': result.get('confidence', 0.0),
                'source_language': source_lang,
                'target_language': target_lang
            }
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return {
                'translated_text': text,
                'confidence': 0.0,
                'source_language': source_lang,
                'target_language': target_lang,
                'error': str(e)
            }
    
    def synthesize_speech(self, text: str, target_language: str, voice_type: str = 'female') -> Dict[str, Any]:
        """
        Synchronous wrapper for speech synthesis
        
        Args:
            text: Text to synthesize
            target_language: Target language
            voice_type: Voice type preference
            
        Returns:
            Dict with synthesis results
        """
        try:
            result = asyncio.run(self.bhashini_client.synthesize_speech(text, target_language, voice_type))
            
            if not result['success']:
                # Fallback to AWS Polly
                result = asyncio.run(self.aws_voice_services.synthesize_speech_fallback(text, target_language, voice_type))
            
            return {
                'audio_url': result.get('audio_url', ''),
                'duration': result.get('duration', 0),
                'language': target_language
            }
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {str(e)}")
            return {
                'audio_url': '',
                'duration': 0,
                'language': target_language,
                'error': str(e)
            }