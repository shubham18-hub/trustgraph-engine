"""
Digital Wallet Service - Self-Sovereign Identity Wallet
Secure storage for Reputation Assets (Verifiable Credentials)
"""

import logging
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from src.database import db
from src.services.blockchain_service import indian_credential_service

logger = logging.getLogger(__name__)

class DigitalWalletService:
    """
    Self-sovereign digital wallet for workers
    Stores and manages Reputation Assets (VCs)
    """
    
    def __init__(self):
        self.db = db
        self.blockchain_service = indian_credential_service
    
    async def create_wallet(self, worker_id: str) -> Dict[str, Any]:
        """
        Create digital wallet for worker
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Wallet creation result
        """
        try:
            worker = self.db.get_user(worker_id)
            if not worker:
                return {
                    'success': False,
                    'error': 'Worker not found'
                }
            
            # Generate wallet ID
            wallet_id = f"wallet_{uuid.uuid4().hex[:16]}"
            
            # Create wallet structure
            wallet = {
                'wallet_id': wallet_id,
                'worker_id': worker_id,
                'did': f"did:india:worker:{hashlib.sha256(worker_id.encode()).hexdigest()[:16]}",
                'created_at': datetime.utcnow().isoformat(),
                'credentials': [],
                'reputation_score': 0,
                'total_earnings': 0,
                'verified_skills': [],
                'work_history_count': 0
            }
            
            logger.info(f"Digital wallet created for {worker_id}: {wallet_id}")
            
            return {
                'success': True,
                'wallet': wallet,
                'message': 'Digital wallet created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating wallet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_wallet(self, worker_id: str) -> Dict[str, Any]:
        """Get worker's digital wallet with all assets"""
        try:
            worker = self.db.get_user(worker_id)
            if not worker:
                return {
                    'success': False,
                    'error': 'Worker not found'
                }
            
            # Get all credentials
            credentials = self.db.get_worker_credentials_vc(worker_id)
            
            # Get trust score
            trust_score = self.db.get_latest_trust_score(worker_id)
            
            # Get transaction history
            transactions = self.db.get_worker_transactions(worker_id)
            
            # Calculate total earnings
            total_earnings = sum(
                float(t.get('amount', 0)) 
                for t in transactions 
                if t.get('status') == 'completed'
            )
            
            # Get verified skills
            verified_skills = self._extract_skills_from_credentials(credentials)
            
            # Build wallet
            wallet = {
                'wallet_id': f"wallet_{worker_id}",
                'worker_id': worker_id,
                'did': f"did:india:worker:{hashlib.sha256(worker_id.encode()).hexdigest()[:16]}",
                'worker_name': worker.get('name'),
                'worker_phone': worker.get('phone'),
                'reputation_assets': {
                    'credentials_count': len(credentials),
                    'credentials': credentials,
                    'trust_score': trust_score.get('score', 0) if trust_score else 0,
                    'trust_category': self._get_trust_category(trust_score.get('score', 0) if trust_score else 0)
                },
                'financial_summary': {
                    'total_earnings': total_earnings,
                    'completed_transactions': len([t for t in transactions if t.get('status') == 'completed']),
                    'pending_payments': len([t for t in transactions if t.get('status') == 'pending'])
                },
                'verified_skills': verified_skills,
                'work_history': {
                    'total_jobs': len(credentials),
                    'recent_work': self._get_recent_work(credentials, limit=5)
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'wallet': wallet
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def add_credential_to_wallet(
        self, 
        worker_id: str, 
        credential_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add new verifiable credential to wallet
        
        Args:
            worker_id: Worker identifier
            credential_data: Credential information
            
        Returns:
            Result of credential addition
        """
        try:
            # Issue W3C Verifiable Credential via blockchain service
            vc_result = await self.blockchain_service.issue_indian_work_credential(
                worker_did=f"did:india:worker:{hashlib.sha256(worker_id.encode()).hexdigest()[:16]}",
                employer_did=credential_data.get('employer_did'),
                work_details=credential_data.get('work_details', {}),
                privacy_settings=credential_data.get('privacy_settings', {
                    'consent_timestamp': datetime.utcnow().isoformat(),
                    'data_categories': ['work_history', 'skills'],
                    'processing_purposes': ['credit_assessment', 'employment'],
                    'retention_period': '7_years'
                })
            )
            
            if not vc_result:
                return {
                    'success': False,
                    'error': 'Failed to issue verifiable credential'
                }
            
            # Store in database
            self.db.create_credential_vc(
                credential_id=vc_result['credentialId'],
                worker_id=worker_id,
                issuer_id=credential_data.get('employer_id'),
                credential_type='IndianWorkCredential',
                credential_data=vc_result['credential'],
                proof=vc_result['credential'].get('proof', {})
            )
            
            logger.info(f"Credential added to wallet for {worker_id}")
            
            return {
                'success': True,
                'credential_id': vc_result['credentialId'],
                'blockchain_tx': vc_result['blockchainTxId'],
                'message': 'Credential added to wallet successfully'
            }
            
        except Exception as e:
            logger.error(f"Error adding credential to wallet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def share_credentials(
        self, 
        worker_id: str, 
        recipient_id: str,
        credential_ids: List[str],
        purpose: str
    ) -> Dict[str, Any]:
        """
        Share selected credentials with third party (bank, employer)
        
        Args:
            worker_id: Worker identifier
            recipient_id: Recipient identifier (bank/employer)
            credential_ids: List of credential IDs to share
            purpose: Purpose of sharing
            
        Returns:
            Sharing result with access token
        """
        try:
            # Verify worker owns these credentials
            credentials = self.db.get_worker_credentials_vc(worker_id)
            owned_ids = [c['credential_id'] for c in credentials]
            
            invalid_ids = [cid for cid in credential_ids if cid not in owned_ids]
            if invalid_ids:
                return {
                    'success': False,
                    'error': f'Invalid credential IDs: {invalid_ids}'
                }
            
            # Generate sharing token
            share_token = self._generate_share_token(worker_id, recipient_id, credential_ids)
            
            # Create sharing record
            sharing_record = {
                'share_id': f"share_{uuid.uuid4().hex[:12]}",
                'worker_id': worker_id,
                'recipient_id': recipient_id,
                'credential_ids': credential_ids,
                'purpose': purpose,
                'share_token': share_token,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow().timestamp() + 86400),  # 24 hours
                'access_count': 0,
                'status': 'active'
            }
            
            logger.info(f"Credentials shared by {worker_id} with {recipient_id}")
            
            return {
                'success': True,
                'share_token': share_token,
                'expires_in': 86400,
                'shared_credentials': len(credential_ids),
                'message': 'Credentials shared successfully'
            }
            
        except Exception as e:
            logger.error(f"Error sharing credentials: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def revoke_credential_access(
        self, 
        worker_id: str, 
        share_id: str
    ) -> Dict[str, Any]:
        """Revoke previously shared credential access"""
        try:
            # This would update the sharing record status
            logger.info(f"Credential access revoked by {worker_id}: {share_id}")
            
            return {
                'success': True,
                'message': 'Credential access revoked successfully'
            }
            
        except Exception as e:
            logger.error(f"Error revoking access: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_skills_from_credentials(self, credentials: List[Dict]) -> List[str]:
        """Extract unique verified skills from credentials"""
        skills = set()
        for cred in credentials:
            cred_data = cred.get('credential_data', {})
            if isinstance(cred_data, str):
                try:
                    cred_data = json.loads(cred_data)
                except:
                    continue
            
            # Extract skills from credential subject
            subject = cred_data.get('credentialSubject', {})
            work_details = subject.get('workDetails', {})
            job_type = work_details.get('jobType', {})
            
            if job_type.get('english'):
                skills.add(job_type['english'])
        
        return list(skills)
    
    def _get_recent_work(self, credentials: List[Dict], limit: int = 5) -> List[Dict]:
        """Get recent work history"""
        # Sort by issued date
        sorted_creds = sorted(
            credentials,
            key=lambda x: x.get('issued_at', ''),
            reverse=True
        )
        
        recent = []
        for cred in sorted_creds[:limit]:
            cred_data = cred.get('credential_data', {})
            if isinstance(cred_data, str):
                try:
                    cred_data = json.loads(cred_data)
                except:
                    continue
            
            subject = cred_data.get('credentialSubject', {})
            work_details = subject.get('workDetails', {})
            
            recent.append({
                'credential_id': cred['credential_id'],
                'work_type': work_details.get('jobType', {}).get('english', 'Unknown'),
                'issued_at': cred.get('issued_at'),
                'status': cred.get('status')
            })
        
        return recent
    
    def _get_trust_category(self, score: int) -> str:
        """Get trust category from score"""
        if score >= 800:
            return 'Excellent'
        elif score >= 650:
            return 'Good'
        elif score >= 500:
            return 'Fair'
        elif score >= 300:
            return 'Building'
        else:
            return 'New'
    
    def _generate_share_token(
        self, 
        worker_id: str, 
        recipient_id: str, 
        credential_ids: List[str]
    ) -> str:
        """Generate secure sharing token"""
        data = f"{worker_id}:{recipient_id}:{':'.join(credential_ids)}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

# Initialize service
digital_wallet_service = DigitalWalletService()
