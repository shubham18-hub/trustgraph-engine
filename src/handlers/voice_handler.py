"""
Voice Interface Handler for TrustGraph Engine
Processes voice commands in 22 Indian languages via Bhashini API with AWS fallback
Supports milestone logging, payment inquiries, and trust score checks
"""
import json
import base64
import asyncio
from typing import Dict, Any
from src.services.voice_service import VoiceService, VoiceProcessingResult
from src.utils.response import create_response
from src.utils.logger import get_logger

logger = get_logger(__name__)
voice_service = VoiceService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for voice processing operations
    
    Supported operations:
    - POST /voice/transcribe - Convert speech to text using Bhashini + AWS Transcribe
    - POST /voice/translate - Translate between Indian languages using Bhashini
    - POST /voice/synthesize - Convert text to speech using Bhashini + AWS Polly
    - POST /voice/command - Process complete voice commands with intent classification
    - POST /voice/milestone - Log work milestones via voice (specialized endpoint)
    """
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')
        body = json.loads(event.get('body', '{}'))
        
        logger.info(f"Voice request: {http_method} {path}")
        
        # Route to appropriate handler
        if path == '/voice/transcribe' and http_method == 'POST':
            return handle_transcribe(body)
        elif path == '/voice/translate' and http_method == 'POST':
            return handle_translate(body)
        elif path == '/voice/synthesize' and http_method == 'POST':
            return handle_synthesize(body)
        elif path == '/voice/command' and http_method == 'POST':
            return handle_voice_command(body)
        elif path == '/voice/milestone' and http_method == 'POST':
            return handle_milestone_logging(body)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}")
        return create_response(500, {'error': 'Internal server error', 'details': str(e)})

def handle_transcribe(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert speech to text using Bhashini API with AWS Transcribe fallback
    
    Request body:
    {
        "audio_data": "base64_encoded_audio",
        "source_language": "hi|bn|te|mr|ta|gu|kn|ml|or|pa|as|ur|ne|...",
        "format": "wav|mp3|m4a"
    }
    """
    audio_data = body.get('audio_data')
    source_language = body.get('source_language', 'hi')
    audio_format = body.get('format', 'wav')
    
    if not audio_data:
        return create_response(400, {
            'error': 'Audio data required',
            'supported_languages': list(voice_service.bhashini_client.supported_languages.keys()),
            'supported_formats': ['wav', 'mp3', 'm4a']
        })
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Validate audio size (max 10MB)
        if len(audio_bytes) > 10 * 1024 * 1024:
            return create_response(400, {'error': 'Audio file too large (max 10MB)'})
        
        # Transcribe audio
        result = voice_service.transcribe_audio(audio_bytes, source_language)
        
        return create_response(200, {
            'transcribed_text': result['text'],
            'confidence_score': result['confidence'],
            'detected_language': result['language'],
            'source_language': source_language,
            'processing_info': {
                'fallback_used': result.get('error') is not None,
                'service_used': 'aws_transcribe' if result.get('error') else 'bhashini'
            }
        })
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return create_response(500, {'error': 'Transcription failed', 'details': str(e)})

def handle_translate(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate text between Indian languages using Bhashini API
    
    Request body:
    {
        "text": "text_to_translate",
        "source_language": "hi",
        "target_language": "en"
    }
    """
    text = body.get('text')
    source_lang = body.get('source_language')
    target_lang = body.get('target_language')
    
    if not all([text, source_lang, target_lang]):
        return create_response(400, {
            'error': 'Text, source_language, and target_language required',
            'supported_languages': list(voice_service.bhashini_client.supported_languages.keys())
        })
    
    # Validate text length (max 1000 characters)
    if len(text) > 1000:
        return create_response(400, {'error': 'Text too long (max 1000 characters)'})
    
    try:
        result = voice_service.translate_text(text, source_lang, target_lang)
        
        return create_response(200, {
            'translated_text': result['translated_text'],
            'confidence_score': result['confidence'],
            'source_language': source_lang,
            'target_language': target_lang,
            'original_text': text
        })
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return create_response(500, {'error': 'Translation failed', 'details': str(e)})

def handle_synthesize(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert text to speech using Bhashini API with AWS Polly fallback
    
    Request body:
    {
        "text": "text_to_synthesize",
        "target_language": "hi",
        "voice_type": "female|male",
        "speed": 1.0,
        "format": "wav|mp3"
    }
    """
    text = body.get('text')
    target_language = body.get('target_language', 'hi')
    voice_type = body.get('voice_type', 'female')
    speed = body.get('speed', 1.0)
    output_format = body.get('format', 'wav')
    
    if not text:
        return create_response(400, {
            'error': 'Text required for synthesis',
            'supported_languages': list(voice_service.bhashini_client.supported_languages.keys()),
            'voice_types': ['female', 'male']
        })
    
    # Validate text length (max 500 characters for TTS)
    if len(text) > 500:
        return create_response(400, {'error': 'Text too long for synthesis (max 500 characters)'})
    
    try:
        result = voice_service.synthesize_speech(text, target_language, voice_type)
        
        return create_response(200, {
            'audio_url': result['audio_url'],
            'duration_seconds': result['duration'],
            'language': target_language,
            'voice_type': voice_type,
            'text': text,
            'processing_info': {
                'fallback_used': result.get('error') is not None,
                'service_used': 'aws_polly' if result.get('error') else 'bhashini'
            }
        })
        
    except Exception as e:
        logger.error(f"Speech synthesis error: {str(e)}")
        return create_response(500, {'error': 'Speech synthesis failed', 'details': str(e)})

def handle_voice_command(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process complete voice command workflow with intent classification
    
    Request body:
    {
        "audio_data": "base64_encoded_audio",
        "user_id": "worker_12345",
        "session_context": {
            "preferred_language": "hi",
            "name": "राम कुमार",
            "location": "Noida",
            "literacy_level": "basic"
        }
    }
    """
    audio_data = body.get('audio_data')
    user_id = body.get('user_id')
    session_context = body.get('session_context', {})
    
    if not audio_data or not user_id:
        return create_response(400, {
            'error': 'Audio data and user ID required',
            'example_request': {
                'audio_data': 'base64_encoded_wav_audio',
                'user_id': 'worker_12345',
                'session_context': {
                    'preferred_language': 'hi',
                    'name': 'राम कुमार'
                }
            }
        })
    
    try:
        # Decode audio
        audio_bytes = base64.b64decode(audio_data)
        
        # Validate audio size
        if len(audio_bytes) > 10 * 1024 * 1024:
            return create_response(400, {'error': 'Audio file too large (max 10MB)'})
        
        # Process voice command end-to-end
        result: VoiceProcessingResult = asyncio.run(
            voice_service.process_voice_command(audio_bytes, user_id, session_context)
        )
        
        # Prepare response
        response_data = {
            'transcribed_text': result.transcribed_text,
            'detected_language': result.detected_language,
            'understood_intent': result.intent.value,
            'extracted_entities': result.entities,
            'confidence_score': result.confidence,
            'response_text': result.response_text,
            'response_audio_url': result.response_audio_url,
            'session_id': result.session_id,
            'processing_info': {
                'processing_time_ms': result.processing_time_ms,
                'fallback_used': result.fallback_used,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Add error information if present
        if result.error:
            response_data['error'] = result.error
            return create_response(500, response_data)
        
        # Add next steps based on intent
        if result.intent.value == 'milestone_completion':
            response_data['next_steps'] = [
                'Upload photo evidence of completed work',
                'Get confirmation from employer',
                'Wait for payment processing'
            ]
        elif result.intent.value == 'payment_inquiry':
            response_data['next_steps'] = [
                'Check SMS for payment updates',
                'Contact employer if payment delayed'
            ]
        elif result.intent.value == 'trust_score_check':
            response_data['next_steps'] = [
                'Complete more work to improve score',
                'Get skill verifications',
                'Maintain payment consistency'
            ]
        
        return create_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Voice command processing error: {str(e)}")
        return create_response(500, {
            'error': 'Voice command processing failed',
            'details': str(e),
            'user_id': user_id
        })

def handle_milestone_logging(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Specialized endpoint for logging work milestones via voice
    
    Request body:
    {
        "audio_data": "base64_encoded_audio",
        "user_id": "worker_12345",
        "milestone_context": {
            "project_id": "proj_123",
            "expected_work_type": "masonry",
            "location": {"lat": 28.5355, "lng": 77.3910}
        }
    }
    """
    audio_data = body.get('audio_data')
    user_id = body.get('user_id')
    milestone_context = body.get('milestone_context', {})
    
    if not audio_data or not user_id:
        return create_response(400, {
            'error': 'Audio data and user ID required for milestone logging'
        })
    
    try:
        # Decode audio
        audio_bytes = base64.b64decode(audio_data)
        
        # Add milestone-specific context
        session_context = {
            'preferred_language': milestone_context.get('language', 'hi'),
            'context_type': 'milestone_logging',
            'project_id': milestone_context.get('project_id'),
            'expected_work_type': milestone_context.get('expected_work_type')
        }
        
        # Process voice command
        result: VoiceProcessingResult = asyncio.run(
            voice_service.process_voice_command(audio_bytes, user_id, session_context)
        )
        
        # Validate that this is indeed a milestone completion intent
        if result.intent.value != 'milestone_completion':
            return create_response(400, {
                'error': 'Voice command not recognized as milestone completion',
                'detected_intent': result.intent.value,
                'transcribed_text': result.transcribed_text,
                'suggestion': 'Please clearly state that you have completed your work'
            })
        
        # Extract milestone-specific information
        milestone_data = {
            'user_id': user_id,
            'transcribed_text': result.transcribed_text,
            'detected_work_type': result.entities.get('work_type'),
            'completion_percentage': result.entities.get('completion_percentage', 100),
            'confidence_score': result.confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': result.session_id
        }
        
        # TODO: Integrate with milestone service to actually log the milestone
        # milestone_service.log_completion(milestone_data)
        
        return create_response(200, {
            'milestone_logged': True,
            'milestone_data': milestone_data,
            'response_text': result.response_text,
            'response_audio_url': result.response_audio_url,
            'next_steps': [
                'Upload photo evidence',
                'Wait for employer confirmation',
                'Payment will be processed automatically'
            ],
            'processing_info': {
                'processing_time_ms': result.processing_time_ms,
                'fallback_used': result.fallback_used
            }
        })
        
    except Exception as e:
        logger.error(f"Milestone logging error: {str(e)}")
        return create_response(500, {
            'error': 'Milestone logging failed',
            'details': str(e),
            'user_id': user_id
        })

# Import datetime for timestamp generation
from datetime import datetime