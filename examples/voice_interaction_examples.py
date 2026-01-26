"""
Voice Interaction Examples for TrustGraph Engine
Demonstrates voice-first milestone logging in 22 Indian languages
"""

import json
import base64
import requests
from typing import Dict, Any

class VoiceInteractionExamples:
    """
    Examples of voice interactions for TrustGraph Engine
    """
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer YOUR_API_TOKEN'
        }
    
    def example_milestone_completion_hindi(self) -> Dict[str, Any]:
        """
        Example: Worker completes masonry work and logs via voice in Hindi
        """
        
        # Simulated audio data (in real scenario, this would be actual audio)
        sample_audio_text = "मैंने अपना राजमिस्त्री का काम पूरा कर दिया है। नींव की खुदाई 100% पूरी हो गई है।"
        
        # Convert text to base64 (simulating audio encoding)
        audio_data = base64.b64encode(sample_audio_text.encode('utf-8')).decode('utf-8')
        
        request_body = {
            "audio_data": audio_data,
            "user_id": "worker_ram_kumar_12345",
            "session_context": {
                "preferred_language": "hi",
                "name": "राम कुमार",
                "location": "Sector 4, Noida",
                "literacy_level": "basic",
                "current_project": "residential_complex_phase2"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/command",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Milestone Completion in Hindi",
            "input_text": sample_audio_text,
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_payment_inquiry_bengali(self) -> Dict[str, Any]:
        """
        Example: Worker inquires about payment in Bengali
        """
        
        sample_audio_text = "আমার টাকা কবে পাবো? গত সপ্তাহের কাজের জন্য পেমেন্ট কবে আসবে?"
        audio_data = base64.b64encode(sample_audio_text.encode('utf-8')).decode('utf-8')
        
        request_body = {
            "audio_data": audio_data,
            "user_id": "worker_rahul_das_67890",
            "session_context": {
                "preferred_language": "bn",
                "name": "রাহুল দাস",
                "location": "Kolkata",
                "literacy_level": "intermediate"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/command",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Payment Inquiry in Bengali",
            "input_text": sample_audio_text,
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_trust_score_check_tamil(self) -> Dict[str, Any]:
        """
        Example: Worker checks trust score in Tamil
        """
        
        sample_audio_text = "என் நம்பிக்கை மதிப்பெண் என்ன? என் கடன் மதிப்பெண் எவ்வளவு?"
        audio_data = base64.b64encode(sample_audio_text.encode('utf-8')).decode('utf-8')
        
        request_body = {
            "audio_data": audio_data,
            "user_id": "worker_murugan_54321",
            "session_context": {
                "preferred_language": "ta",
                "name": "முருகன்",
                "location": "Chennai",
                "literacy_level": "advanced"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/command",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Trust Score Check in Tamil",
            "input_text": sample_audio_text,
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_skill_verification_telugu(self) -> Dict[str, Any]:
        """
        Example: Worker requests skill verification in Telugu
        """
        
        sample_audio_text = "నా నైపుణ్యం ధృవీకరణ చేయాలి। నేను ప్లంబర్ గా 5 సంవత్సరాల అనుభవం ఉంది।"
        audio_data = base64.b64encode(sample_audio_text.encode('utf-8')).decode('utf-8')
        
        request_body = {
            "audio_data": audio_data,
            "user_id": "worker_venkat_98765",
            "session_context": {
                "preferred_language": "te",
                "name": "వెంకట్",
                "location": "Hyderabad",
                "literacy_level": "basic"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/command",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Skill Verification in Telugu",
            "input_text": sample_audio_text,
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_specialized_milestone_logging(self) -> Dict[str, Any]:
        """
        Example: Specialized milestone logging endpoint usage
        """
        
        sample_audio_text = "मैंने पेंटिंग का काम पूरा कर दिया है। दो कमरों की दीवारों पर पेंट लगाना 100% हो गया।"
        audio_data = base64.b64encode(sample_audio_text.encode('utf-8')).decode('utf-8')
        
        request_body = {
            "audio_data": audio_data,
            "user_id": "worker_suresh_11111",
            "milestone_context": {
                "project_id": "proj_residential_complex_123",
                "expected_work_type": "painting",
                "location": {"lat": 28.5355, "lng": 77.3910},
                "language": "hi"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/milestone",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Specialized Milestone Logging",
            "input_text": sample_audio_text,
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_transcription_only(self) -> Dict[str, Any]:
        """
        Example: Audio transcription without intent processing
        """
        
        sample_audio_text = "मुझे अपने काम के बारे में जानकारी चाहिए।"
        audio_data = base64.b64encode(sample_audio_text.encode('utf-8')).decode('utf-8')
        
        request_body = {
            "audio_data": audio_data,
            "source_language": "hi",
            "format": "wav"
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/transcribe",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Audio Transcription Only",
            "input_text": sample_audio_text,
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_text_to_speech(self) -> Dict[str, Any]:
        """
        Example: Text to speech synthesis
        """
        
        request_body = {
            "text": "आपका काम पूरा होने की जानकारी मिली है। कृपया फोटो अपलोड करें।",
            "target_language": "hi",
            "voice_type": "female",
            "format": "wav"
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/synthesize",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Text to Speech Synthesis",
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def example_translation(self) -> Dict[str, Any]:
        """
        Example: Text translation between Indian languages
        """
        
        request_body = {
            "text": "मैंने अपना काम पूरा कर दिया है।",
            "source_language": "hi",
            "target_language": "en"
        }
        
        response = requests.post(
            f"{self.api_base_url}/voice/translate",
            headers=self.headers,
            json=request_body
        )
        
        return {
            "example": "Hindi to English Translation",
            "request": request_body,
            "response": response.json() if response.status_code == 200 else response.text
        }
    
    def run_all_examples(self) -> Dict[str, Any]:
        """
        Run all voice interaction examples
        """
        
        examples = {
            "milestone_completion_hindi": self.example_milestone_completion_hindi(),
            "payment_inquiry_bengali": self.example_payment_inquiry_bengali(),
            "trust_score_check_tamil": self.example_trust_score_check_tamil(),
            "skill_verification_telugu": self.example_skill_verification_telugu(),
            "specialized_milestone_logging": self.example_specialized_milestone_logging(),
            "transcription_only": self.example_transcription_only(),
            "text_to_speech": self.example_text_to_speech(),
            "translation": self.example_translation()
        }
        
        return examples

# Usage example
if __name__ == "__main__":
    # Initialize with your API Gateway URL
    api_url = "https://your-api-gateway-url.amazonaws.com/prod"
    
    examples = VoiceInteractionExamples(api_url)
    
    # Run individual examples
    print("=== Milestone Completion in Hindi ===")
    result = examples.example_milestone_completion_hindi()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== Payment Inquiry in Bengali ===")
    result = examples.example_payment_inquiry_bengali()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== Trust Score Check in Tamil ===")
    result = examples.example_trust_score_check_tamil()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Run all examples
    print("\n=== All Examples ===")
    all_results = examples.run_all_examples()
    print(json.dumps(all_results, indent=2, ensure_ascii=False))