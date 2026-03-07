"""
Digital Wallet API Handler
Endpoints for self-sovereign identity wallet management
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from src.services.digital_wallet_service import digital_wallet_service
from src.utils.response import create_response

router = APIRouter(prefix="/api/wallet", tags=["Digital Wallet"])

class AddCredentialRequest(BaseModel):
    employer_id: str
    employer_did: str
    work_details: dict
    privacy_settings: Optional[dict] = None

class ShareCredentialsRequest(BaseModel):
    recipient_id: str
    credential_ids: List[str]
    purpose: str

@router.post("/{worker_id}/create")
async def create_wallet(worker_id: str):
    """Create digital wallet for worker"""
    try:
        result = await digital_wallet_service.create_wallet(worker_id)
        
        if result['success']:
            return create_response(201, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.get("/{worker_id}")
async def get_wallet(worker_id: str):
    """Get worker's digital wallet with all reputation assets"""
    try:
        result = await digital_wallet_service.get_wallet(worker_id)
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(404, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.post("/{worker_id}/credentials")
async def add_credential(worker_id: str, request: AddCredentialRequest):
    """Add new verifiable credential to wallet"""
    try:
        result = await digital_wallet_service.add_credential_to_wallet(
            worker_id=worker_id,
            credential_data={
                'employer_id': request.employer_id,
                'employer_did': request.employer_did,
                'work_details': request.work_details,
                'privacy_settings': request.privacy_settings
            }
        )
        
        if result['success']:
            return create_response(201, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.post("/{worker_id}/share")
async def share_credentials(worker_id: str, request: ShareCredentialsRequest):
    """Share credentials with third party (bank, employer)"""
    try:
        result = await digital_wallet_service.share_credentials(
            worker_id=worker_id,
            recipient_id=request.recipient_id,
            credential_ids=request.credential_ids,
            purpose=request.purpose
        )
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.delete("/{worker_id}/share/{share_id}")
async def revoke_access(worker_id: str, share_id: str):
    """Revoke previously shared credential access"""
    try:
        result = await digital_wallet_service.revoke_credential_access(
            worker_id=worker_id,
            share_id=share_id
        )
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})
