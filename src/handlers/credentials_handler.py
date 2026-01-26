"""
Verifiable Credentials Handler for TrustGraph Engine
Manages W3C-compliant credential issuance and verification
"""
import json
from typing import Dict, Any
from src.services.credentials_service import CredentialsService
from src.utils.response import create_response
from src.utils.logger import get_logger
from src.utils.auth import verify_jwt_token

logger = get_logger(__name__)
credentials_service = CredentialsService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for credential operations
    
    Supported operations:
    - POST /credentials/issue - Issue new work credential
    - GET /credentials/{worker_id} - Get worker's credentials
    - PUT /credentials/{credential_id}/verify - Verify credential
    """
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')
        path_parameters = event.get('pathParameters', {})
        body = json.loads(event.get('body', '{}'))
        headers = event.get('headers', {})
        
        # Verify JWT token for authenticated endpoints
        auth_result = verify_jwt_token(headers.get('Authorization'))
        if not auth_result['valid']:
            return create_response(401, {'error': 'Invalid or missing token'})
        
        user_context = auth_result['user']
        logger.info(f"Credentials request: {http_method} {path} by user {user_context['user_id']}")
        
        if path == '/credentials/issue' and http_method == 'POST':
            return handle_issue_credential(body, user_context)
        elif path.startswith('/credentials/') and http_method == 'GET':
            worker_id = path_parameters.get('worker_id')
            return handle_get_credentials(worker_id, user_context)
        elif '/verify' in path and http_method == 'PUT':
            credential_id = path_parameters.get('credential_id')
            return handle_verify_credential(credential_id, body, user_context)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Credentials error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def handle_issue_credential(body: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Issue a new W3C Verifiable Credential for completed work"""
    required_fields = ['worker_id', 'work_details', 'employer_signature']
    
    if not all(field in body for field in required_fields):
        return create_response(400, {'error': f'Required fields: {required_fields}'})
    
    # Verify issuer has permission to issue credentials
    if user_context['role'] not in ['employer', 'verifier']:
        return create_response(403, {'error': 'Insufficient permissions to issue credentials'})
    
    credential_data = {
        'worker_id': body['worker_id'],
        'work_details': body['work_details'],
        'issuer_id': user_context['user_id'],
        'employer_signature': body['employer_signature']
    }
    
    result = credentials_service.issue_credential(credential_data)
    return create_response(201, result)

def handle_get_credentials(worker_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Get all credentials for a worker (with privacy controls)"""
    if not worker_id:
        return create_response(400, {'error': 'Worker ID required'})
    
    # Privacy check: users can only access their own credentials unless they're verifiers
    if user_context['user_id'] != worker_id and user_context['role'] != 'verifier':
        return create_response(403, {'error': 'Access denied'})
    
    result = credentials_service.get_worker_credentials(worker_id)
    return create_response(200, result)

def handle_verify_credential(credential_id: str, body: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the cryptographic integrity of a credential"""
    if not credential_id:
        return create_response(400, {'error': 'Credential ID required'})
    
    result = credentials_service.verify_credential(credential_id)
    return create_response(200, result)