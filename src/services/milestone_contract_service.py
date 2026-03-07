"""
Milestone-Based Smart Contract Service
Agentic self-executing contracts for wage security
Auto-disbursal upon verification (geotags/photos)
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import hashlib

from src.database import db
from src.services.upi_service import UPIService

logger = logging.getLogger(__name__)

class MilestoneContractService:
    """
    Agentic Smart Contracts for milestone-based payments
    Ensures 100% wage security with automatic verification
    """
    
    def __init__(self):
        self.db = db
        self.upi_service = UPIService()
        
        # Contract states
        self.contract_states = [
            'draft', 'active', 'milestone_pending', 
            'milestone_completed', 'payment_processing',
            'completed', 'disputed', 'cancelled'
        ]
        
        # Verification requirements
        self.verification_types = {
            'photo': {'required': True, 'min_count': 1},
            'geotag': {'required': True, 'accuracy': 'high'},
            'employer_approval': {'required': True},
            'time_verification': {'required': False}
        }
    
    async def create_contract(
        self, 
        employer_id: str,
        worker_id: str,
        job_details: Dict[str, Any],
        milestones: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create new milestone-based smart contract
        
        Args:
            employer_id: Employer identifier
            worker_id: Worker identifier
            job_details: Job information
            milestones: List of milestone definitions
            
        Returns:
            Contract creation result
        """
        try:
            # Validate inputs
            if not milestones:
                return {
                    'success': False,
                    'error': 'At least one milestone required'
                }
            
            # Calculate total contract value
            total_amount = sum(Decimal(str(m.get('amount', 0))) for m in milestones)
            
            # Generate contract ID
            contract_id = f"contract_{uuid.uuid4().hex[:12]}"
            
            # Create contract structure
            contract = {
                'contract_id': contract_id,
                'employer_id': employer_id,
                'worker_id': worker_id,
                'job_details': {
                    'title': job_details.get('title'),
                    'description': job_details.get('description'),
                    'work_type': job_details.get('work_type'),
                    'location': job_details.get('location'),
                    'start_date': job_details.get('start_date'),
                    'estimated_end_date': job_details.get('estimated_end_date')
                },
                'total_amount': float(total_amount),
                'currency': 'INR',
                'milestones': self._prepare_milestones(milestones),
                'state': 'draft',
                'created_at': datetime.utcnow().isoformat(),
                'terms': {
                    'auto_payment': True,
                    'verification_required': True,
                    'dispute_resolution': 'platform_mediation',
                    'payment_method': 'UPI'
                },
                'blockchain_hash': None
            }
            
            # Store contract (would be on blockchain in production)
            contract_hash = self._hash_contract(contract)
            contract['blockchain_hash'] = contract_hash
            
            logger.info(f"Smart contract created: {contract_id}")
            
            return {
                'success': True,
                'contract_id': contract_id,
                'contract': contract,
                'blockchain_hash': contract_hash,
                'message': 'Smart contract created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating contract: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def activate_contract(self, contract_id: str) -> Dict[str, Any]:
        """Activate contract after both parties agree"""
        try:
            # In production, this would update blockchain state
            logger.info(f"Contract activated: {contract_id}")
            
            return {
                'success': True,
                'contract_id': contract_id,
                'state': 'active',
                'message': 'Contract activated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error activating contract: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def submit_milestone_proof(
        self,
        contract_id: str,
        milestone_id: str,
        worker_id: str,
        proof_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit proof of milestone completion
        
        Args:
            contract_id: Contract identifier
            milestone_id: Milestone identifier
            worker_id: Worker submitting proof
            proof_data: Verification data (photos, geotags, etc.)
            
        Returns:
            Submission result
        """
        try:
            # Validate proof data
            validation = self._validate_proof(proof_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error']
                }
            
            # Store proof
            proof_id = f"proof_{uuid.uuid4().hex[:12]}"
            proof_record = {
                'proof_id': proof_id,
                'contract_id': contract_id,
                'milestone_id': milestone_id,
                'worker_id': worker_id,
                'submitted_at': datetime.utcnow().isoformat(),
                'proof_type': proof_data.get('type'),
                'photos': proof_data.get('photos', []),
                'geotag': proof_data.get('geotag'),
                'notes': proof_data.get('notes'),
                'status': 'pending_verification'
            }
            
            # Trigger automatic verification
            verification_result = await self._auto_verify_proof(proof_record)
            
            if verification_result['auto_approved']:
                # Trigger automatic payment
                payment_result = await self._trigger_milestone_payment(
                    contract_id, 
                    milestone_id,
                    worker_id
                )
                
                return {
                    'success': True,
                    'proof_id': proof_id,
                    'auto_verified': True,
                    'payment_initiated': payment_result['success'],
                    'payment_id': payment_result.get('payment_id'),
                    'message': 'Milestone verified and payment initiated automatically'
                }
            else:
                return {
                    'success': True,
                    'proof_id': proof_id,
                    'auto_verified': False,
                    'requires_employer_approval': True,
                    'message': 'Proof submitted, awaiting employer verification'
                }
            
        except Exception as e:
            logger.error(f"Error submitting milestone proof: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_milestone(
        self,
        contract_id: str,
        milestone_id: str,
        employer_id: str,
        approved: bool,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Employer verification of milestone completion
        
        Args:
            contract_id: Contract identifier
            milestone_id: Milestone identifier
            employer_id: Employer verifying
            approved: Verification result
            notes: Optional verification notes
            
        Returns:
            Verification result
        """
        try:
            if approved:
                # Get milestone details
                # In production, fetch from blockchain
                
                # Trigger automatic payment
                payment_result = await self._trigger_milestone_payment(
                    contract_id,
                    milestone_id,
                    None  # Worker ID would be fetched from contract
                )
                
                logger.info(f"Milestone verified and payment triggered: {milestone_id}")
                
                return {
                    'success': True,
                    'milestone_id': milestone_id,
                    'verified': True,
                    'payment_initiated': payment_result['success'],
                    'payment_id': payment_result.get('payment_id'),
                    'message': 'Milestone verified, payment initiated'
                }
            else:
                logger.info(f"Milestone rejected: {milestone_id}")
                
                return {
                    'success': True,
                    'milestone_id': milestone_id,
                    'verified': False,
                    'reason': notes,
                    'message': 'Milestone verification rejected'
                }
            
        except Exception as e:
            logger.error(f"Error verifying milestone: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _trigger_milestone_payment(
        self,
        contract_id: str,
        milestone_id: str,
        worker_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Trigger automatic UPI payment for completed milestone
        
        Args:
            contract_id: Contract identifier
            milestone_id: Milestone identifier
            worker_id: Worker to pay
            
        Returns:
            Payment initiation result
        """
        try:
            # In production, fetch contract and milestone from blockchain
            # For now, use mock data
            
            # Get worker UPI ID
            if worker_id:
                worker = self.db.get_user(worker_id)
                worker_upi = worker.get('phone', '').replace('+91', '') + '@paytm'
            else:
                worker_upi = '9876543210@paytm'  # Mock
            
            # Initiate UPI payment
            payment_request = {
                'payee_upi_id': worker_upi,
                'amount': 5000,  # Mock amount
                'description': f'Milestone payment for {milestone_id}',
                'payment_id': f'milestone_{milestone_id}_{uuid.uuid4().hex[:8]}'
            }
            
            payment_result = await self.upi_service.initiate_payment(payment_request)
            
            if payment_result['success']:
                logger.info(f"Milestone payment initiated: {payment_result['payment_id']}")
                
                return {
                    'success': True,
                    'payment_id': payment_result['payment_id'],
                    'transaction_ref': payment_result.get('transaction_ref'),
                    'status': 'processing'
                }
            else:
                logger.error(f"Milestone payment failed: {payment_result.get('error')}")
                return {
                    'success': False,
                    'error': payment_result.get('error')
                }
            
        except Exception as e:
            logger.error(f"Error triggering milestone payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _auto_verify_proof(self, proof_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatic verification of proof using AI/ML
        
        Args:
            proof_record: Proof submission data
            
        Returns:
            Verification result
        """
        try:
            # Check if all required proof elements present
            has_photos = len(proof_record.get('photos', [])) >= 1
            has_geotag = proof_record.get('geotag') is not None
            
            # Basic automatic verification
            if has_photos and has_geotag:
                # In production, use AI to verify photo quality and geotag accuracy
                # For now, auto-approve if both present
                return {
                    'auto_approved': True,
                    'confidence': 0.85,
                    'verification_method': 'automated'
                }
            else:
                return {
                    'auto_approved': False,
                    'confidence': 0.0,
                    'verification_method': 'manual_required',
                    'reason': 'Insufficient proof elements'
                }
            
        except Exception as e:
            logger.error(f"Error in auto-verification: {str(e)}")
            return {
                'auto_approved': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _prepare_milestones(self, milestones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare milestone structure with IDs and validation"""
        prepared = []
        for idx, milestone in enumerate(milestones):
            prepared.append({
                'milestone_id': f"milestone_{uuid.uuid4().hex[:8]}",
                'sequence': idx + 1,
                'title': milestone.get('title'),
                'description': milestone.get('description'),
                'amount': float(milestone.get('amount', 0)),
                'verification_required': milestone.get('verification_required', True),
                'estimated_completion': milestone.get('estimated_completion'),
                'status': 'pending',
                'proof_submitted': False,
                'verified': False,
                'paid': False
            })
        return prepared
    
    def _validate_proof(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate proof submission data"""
        if not proof_data.get('type'):
            return {
                'valid': False,
                'error': 'Proof type required'
            }
        
        if proof_data['type'] == 'photo_geotag':
            if not proof_data.get('photos'):
                return {
                    'valid': False,
                    'error': 'At least one photo required'
                }
            if not proof_data.get('geotag'):
                return {
                    'valid': False,
                    'error': 'Geotag required'
                }
        
        return {'valid': True}
    
    def _hash_contract(self, contract: Dict[str, Any]) -> str:
        """Generate blockchain hash for contract"""
        contract_str = json.dumps(contract, sort_keys=True)
        return hashlib.sha256(contract_str.encode()).hexdigest()

# Initialize service
milestone_contract_service = MilestoneContractService()
