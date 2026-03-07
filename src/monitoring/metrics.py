"""CloudWatch monitoring and metrics collection"""

import time
from datetime import datetime
from typing import Dict, Any
import json

class MetricsCollector:
    """Collect and track system metrics"""
    
    def __init__(self):
        self.metrics = {
            'voice_commands': [],
            'credentials_issued': [],
            'trust_scores': [],
            'payments': []
        }
    
    def track_voice_command(self, success: bool, latency_ms: float, language: str):
        """Track voice command metrics"""
        self.metrics['voice_commands'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'success': success,
            'latency_ms': latency_ms,
            'language': language
        })
    
    def track_credential_issuance(self, latency_ms: float, credential_type: str):
        """Track credential issuance metrics"""
        self.metrics['credentials_issued'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'latency_ms': latency_ms,
            'type': credential_type
        })
    
    def track_trust_score(self, computation_time_ms: float, score: int):
        """Track trust score calculation metrics"""
        self.metrics['trust_scores'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'computation_time_ms': computation_time_ms,
            'score': score
        })
    
    def track_payment(self, success: bool, amount: float, method: str):
        """Track payment completion metrics"""
        self.metrics['payments'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'success': success,
            'amount': amount,
            'method': method
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        voice_success_rate = sum(1 for m in self.metrics['voice_commands'] if m['success']) / max(len(self.metrics['voice_commands']), 1)
        avg_credential_latency = sum(m['latency_ms'] for m in self.metrics['credentials_issued']) / max(len(self.metrics['credentials_issued']), 1)
        avg_trust_score_time = sum(m['computation_time_ms'] for m in self.metrics['trust_scores']) / max(len(self.metrics['trust_scores']), 1)
        payment_success_rate = sum(1 for m in self.metrics['payments'] if m['success']) / max(len(self.metrics['payments']), 1)
        
        return {
            'voice_command_success_rate': voice_success_rate,
            'avg_credential_issuance_latency_ms': avg_credential_latency,
            'avg_trust_score_computation_ms': avg_trust_score_time,
            'payment_completion_rate': payment_success_rate,
            'total_voice_commands': len(self.metrics['voice_commands']),
            'total_credentials_issued': len(self.metrics['credentials_issued']),
            'total_trust_scores': len(self.metrics['trust_scores']),
            'total_payments': len(self.metrics['payments'])
        }

metrics_collector = MetricsCollector()
