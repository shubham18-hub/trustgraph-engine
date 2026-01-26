"""
Logging utilities for TrustGraph Engine
Structured logging with correlation IDs for request tracing
"""

import logging
import json
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import contextvars

# Context variable for correlation ID
correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id')

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        
        # Get correlation ID from context
        try:
            corr_id = correlation_id.get()
        except LookupError:
            corr_id = str(uuid.uuid4())
        
        # Build log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': corr_id,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(name)
    
    # Configure logger if not already configured
    if not logger.handlers:
        # Set log level from environment
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        logger.setLevel(getattr(logging, log_level))
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(logger.level)
        
        # Set structured formatter
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    return logger

def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """
    Set correlation ID for current context
    
    Args:
        corr_id: Correlation ID to set (generates new if None)
        
    Returns:
        Set correlation ID
    """
    
    if corr_id is None:
        corr_id = str(uuid.uuid4())
    
    correlation_id.set(corr_id)
    return corr_id

def get_correlation_id() -> str:
    """
    Get correlation ID from current context
    
    Returns:
        Current correlation ID or new one if not set
    """
    
    try:
        return correlation_id.get()
    except LookupError:
        return set_correlation_id()

def log_api_request(logger: logging.Logger, event: Dict[str, Any]) -> None:
    """
    Log API request details
    
    Args:
        logger: Logger instance
        event: Lambda event dict
    """
    
    # Extract request details
    method = event.get('httpMethod', 'UNKNOWN')
    path = event.get('path', 'UNKNOWN')
    source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'UNKNOWN')
    user_agent = event.get('headers', {}).get('User-Agent', 'UNKNOWN')
    
    # Set correlation ID from request headers or generate new
    request_id = event.get('requestContext', {}).get('requestId')
    corr_id = event.get('headers', {}).get('X-Correlation-ID', request_id)
    set_correlation_id(corr_id)
    
    logger.info(
        f"API Request: {method} {path}",
        extra={
            'event_type': 'api_request',
            'http_method': method,
            'path': path,
            'source_ip': source_ip,
            'user_agent': user_agent,
            'request_id': request_id
        }
    )

def log_api_response(logger: logging.Logger, status_code: int, processing_time_ms: float) -> None:
    """
    Log API response details
    
    Args:
        logger: Logger instance
        status_code: HTTP status code
        processing_time_ms: Processing time in milliseconds
    """
    
    logger.info(
        f"API Response: {status_code} ({processing_time_ms:.2f}ms)",
        extra={
            'event_type': 'api_response',
            'status_code': status_code,
            'processing_time_ms': processing_time_ms,
            'success': 200 <= status_code < 300
        }
    )

def log_business_event(logger: logging.Logger, event_type: str, data: Dict[str, Any]) -> None:
    """
    Log business events for analytics
    
    Args:
        logger: Logger instance
        event_type: Type of business event
        data: Event data
    """
    
    logger.info(
        f"Business Event: {event_type}",
        extra={
            'event_type': 'business_event',
            'business_event_type': event_type,
            **data
        }
    )