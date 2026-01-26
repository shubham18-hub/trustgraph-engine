"""
HTTP Response utilities for TrustGraph Engine
Standardized response formatting for API Gateway
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    cors_enabled: bool = True
) -> Dict[str, Any]:
    """
    Create standardized HTTP response for API Gateway
    
    Args:
        status_code: HTTP status code
        body: Response body data
        headers: Additional headers
        cors_enabled: Enable CORS headers
        
    Returns:
        API Gateway compatible response dict
    """
    
    # Default headers
    response_headers = {
        'Content-Type': 'application/json'
    }
    
    # Add CORS headers if enabled
    if cors_enabled:
        response_headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
        })
    
    # Add custom headers
    if headers:
        response_headers.update(headers)
    
    # Add metadata to response body
    response_body = {
        **body,
        'timestamp': datetime.utcnow().isoformat(),
        'status_code': status_code
    }
    
    # Add success flag
    response_body['success'] = 200 <= status_code < 300
    
    return {
        'statusCode': status_code,
        'headers': response_headers,
        'body': json.dumps(response_body, ensure_ascii=False, default=str)
    }

def create_error_response(
    status_code: int,
    error_message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        status_code: HTTP status code
        error_message: Human readable error message
        error_code: Machine readable error code
        details: Additional error details
        
    Returns:
        API Gateway compatible error response
    """
    
    error_body = {
        'error': error_message,
        'error_code': error_code or f'ERR_{status_code}',
    }
    
    if details:
        error_body['details'] = details
    
    return create_response(status_code, error_body)

def create_success_response(
    data: Dict[str, Any],
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        API Gateway compatible success response
    """
    
    response_body = {**data}
    
    if message:
        response_body['message'] = message
    
    return create_response(200, response_body)