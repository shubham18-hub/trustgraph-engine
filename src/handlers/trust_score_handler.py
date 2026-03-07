"""
Trust Score API Handler
Endpoints for Resilience Score calculation and management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from src.services.trust_score_service import trust_score_service
from src.utils.response import create_response

router = APIRouter(prefix="/api/trust-score", tags=["Trust Score"])

@router.get("/{worker_id}")
async def get_trust_score(worker_id: str):
    """Get current trust/resilience score for worker"""
    try:
        result = await trust_score_service.calculate_resilience_score(worker_id)
        
        if result['success']:
            return create_response(200, result)
        else:
            return create_response(404, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.post("/{worker_id}/calculate")
async def calculate_trust_score(worker_id: str):
    """Recalculate trust score for worker"""
    try:
        result = await trust_score_service.calculate_resilience_score(worker_id)
        
        if result['success']:
            return create_response(200, {
                'message': 'Trust score calculated successfully',
                **result
            })
        else:
            return create_response(400, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})

@router.get("/{worker_id}/credit-eligibility")
async def check_credit_eligibility(worker_id: str):
    """Check credit/loan eligibility based on trust score"""
    try:
        result = await trust_score_service.calculate_resilience_score(worker_id)
        
        if result['success']:
            return create_response(200, {
                'worker_id': worker_id,
                'resilience_score': result['resilience_score'],
                'credit_eligibility': result['credit_eligibility']
            })
        else:
            return create_response(404, {'error': result.get('error')})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})
