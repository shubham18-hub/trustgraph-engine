"""
Milestone Contract API Handler
Endpoints for agentic smart contracts and milestone-based payments
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from src.services.milestone_contract_service import milestone_contract_service
from src.utils.response import create_response

router = APIRouter(prefix="/api/contracts", tags=["Milestone Contracts"])

class MilestoneDefinition(BaseModel):
    title: str
    description: str
    amount: float
    verification_required: bool = True
    estimated_completion: Optional[str] = None

class CreateContractRequest(BaseModel):
    employer_id: str
    worker_id: str
    job_details: Dict[str, Any]
    milestones: List[MilestoneDefinition]

class SubmitProofRequest(BaseModel):
    worker_id: str
    proof_type: str
    photos: List[str]
    geotag: Optional[Dict[str, float]] = None
    notes: Optional[str] = None

class VerifyMilestoneRequest(BaseModel):
    employer_id: str
    approved: bool
    notes: Optional[str] = None

@router.post("/create")
async def create_contract(request: CreateContractRequest):
    """Create new milestone-based smart contract"""
    try:
        result = await milestone_contract_service.create_contract(
            employer_id=request.employer_id,
            worker_id=request.worker_id,
            job_details=request.job_details,
            milestones=[m.dict() for m in request.milestones]
        )
        
        if result['success']:
            return create_response(201, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.post("/{contract_id}/activate")
async def activate_contract(contract_id: str):
    """Activate contract after both parties agree"""
    try:
        result = await milestone_contract_service.activate_contract(contract_id)
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.post("/{contract_id}/milestones/{milestone_id}/submit-proof")
async def submit_milestone_proof(
    contract_id: str,
    milestone_id: str,
    request: SubmitProofRequest
):
    """Submit proof of milestone completion (photos, geotags)"""
    try:
        result = await milestone_contract_service.submit_milestone_proof(
            contract_id=contract_id,
            milestone_id=milestone_id,
            worker_id=request.worker_id,
            proof_data={
                'type': request.proof_type,
                'photos': request.photos,
                'geotag': request.geotag,
                'notes': request.notes
            }
        )
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.post("/{contract_id}/milestones/{milestone_id}/verify")
async def verify_milestone(
    contract_id: str,
    milestone_id: str,
    request: VerifyMilestoneRequest
):
    """Employer verification of milestone completion"""
    try:
        result = await milestone_contract_service.verify_milestone(
            contract_id=contract_id,
            milestone_id=milestone_id,
            employer_id=request.employer_id,
            approved=request.approved,
            notes=request.notes
        )
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})
