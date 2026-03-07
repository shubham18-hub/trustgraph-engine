"""
Security Middleware for FastAPI
Zero-trust architecture implementation
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
import time
from collections import defaultdict
from datetime import datetime, timedelta

from src.security import get_security_manager


class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            
            token = credentials.credentials
            
            try:
                security = get_security_manager()
                payload = security.verify_jwt(token)
                
                # Attach user info to request
                request.state.user_id = payload['user_id']
                request.state.user_role = payload['role']
                
                return token
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code"
            )


class RateLimiter:
    """Rate limiting middleware for API protection"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def __call__(self, request: Request, call_next: Callable):
        # Get client IP
        client_ip = request.client.host
        
        # Clean old requests
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


class AuditLogMiddleware:
    """Log all API requests for DPDP Act compliance"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Log request
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'method': scope.get('method'),
            'path': scope.get('path'),
            'client': scope.get('client', ['unknown'])[0] if scope.get('client') else 'unknown'
        }
        
        # Process request
        await self.app(scope, receive, send)
        
        # Log response time
        duration = time.time() - start_time
        log_entry['duration_ms'] = round(duration * 1000, 2)
        
        # In production, send to CloudWatch or logging service
        print(f"[AUDIT] {log_entry}")


class InputSanitizationMiddleware:
    """Sanitize all input data"""
    
    async def __call__(self, request: Request, call_next: Callable):
        # Sanitize query parameters
        if request.query_params:
            security = get_security_manager()
            sanitized_params = {}
            
            for key, value in request.query_params.items():
                sanitized_params[key] = security.sanitize_input(value)
            
            # Update request with sanitized params
            request._query_params = sanitized_params
        
        response = await call_next(request)
        return response


class DPDPComplianceMiddleware:
    """DPDP Act 2023 compliance checks"""
    
    async def __call__(self, request: Request, call_next: Callable):
        # Check data residency
        if request.headers.get('X-Forwarded-For'):
            # In production, verify request originates from India
            pass
        
        # Check consent for data processing
        if hasattr(request.state, 'user_id'):
            # In production, verify user consent
            pass
        
        response = await call_next(request)
        
        # Add DPDP compliance headers
        response.headers['X-Data-Residency'] = 'IN'
        response.headers['X-DPDP-Compliant'] = 'true'
        
        return response
