"""
Input sanitization middleware for comprehensive security validation.
"""

import re
import json
import bleach
import logging
from typing import Any, Dict, List, Union, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import AppSettings

logger = logging.getLogger(__name__)


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for sanitizing and validating all input data."""
    
    def __init__(self, app, settings: Optional[AppSettings] = None):
        """Initialize input sanitization middleware."""
        super().__init__(app)
        self.settings = settings
        
        # Configure bleach for HTML sanitization
        self.allowed_tags = []  # No HTML tags allowed
        self.allowed_attributes = {}
        
        # Patterns for various validations
        self.sql_injection_patterns = [
            r'(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bcreate\b|\balter\b)',
            r'(--|\/\*|\*\/)',
            r'(\bor\b\s+\d+\s*=\s*\d+|\band\b\s+\d+\s*=\s*\d+)',
            r'(\bexec\b|\bexecute\b)',
        ]
        
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
        ]
        
        # Maximum lengths for different types
        self.max_lengths = {
            'short_text': 255,
            'medium_text': 1000,
            'long_text': 10000000,
            'thread_id': 100,
            'model_name': 50,
            'provider': 20,
        }
        
        # Paths that require minimal sanitization (for binary data, etc.)
        self.minimal_sanitization_paths = {
            '/docs', '/redoc', '/openapi.json', '/health'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through sanitization pipeline."""
        try:
            # Skip sanitization for certain paths
            if request.url.path in self.minimal_sanitization_paths:
                return await call_next(request)
            
            # Sanitize request data
            await self._sanitize_request(request)
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Input sanitization error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid input data", "detail": "Input validation failed"}
            )
    
    async def _sanitize_request(self, request: Request):
        """Sanitize all request data including headers, query params, and body."""
        # Sanitize headers
        self._sanitize_headers(request)
        
        # Sanitize query parameters
        self._sanitize_query_params(request)
        
        # Sanitize body if present
        if request.method in ['POST', 'PUT', 'PATCH']:
            await self._sanitize_body(request)
    
    def _sanitize_headers(self, request: Request):
        """Sanitize request headers."""
        dangerous_headers = ['x-forwarded-for', 'user-agent', 'referer']
        
        for header_name in dangerous_headers:
            if header_name in request.headers:
                header_value = request.headers[header_name]
                sanitized_value = self._sanitize_string(header_value, max_length=500)
                # Note: Can't modify headers in FastAPI middleware, just validate
                if self._contains_malicious_patterns(header_value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid characters in header: {header_name}"
                    )
    
    def _sanitize_query_params(self, request: Request):
        """Sanitize query parameters."""
        for param_name, param_value in request.query_params.items():
            if isinstance(param_value, str):
                sanitized = self._sanitize_string(param_value, max_length=500)
                if self._contains_malicious_patterns(param_value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid characters in query parameter: {param_name}"
                    )
    
    async def _sanitize_body(self, request: Request):
        """Sanitize request body data."""
        try:
            # Read the body
            body = await request.body()
            if not body:
                return
            
            # Handle JSON content
            if request.headers.get('content-type', '').startswith('application/json'):
                try:
                    json_data = json.loads(body)
                    sanitized_data = self._sanitize_json_recursively(json_data)
                    
                    # Store sanitized data back (Note: This is complex in FastAPI)
                    # For now, we validate and raise errors for malicious content
                    
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON format"
                    )
            
            # Handle form data
            elif request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
                # Parse and validate form data
                body_str = body.decode('utf-8')
                if self._contains_malicious_patterns(body_str):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid characters in form data"
                    )
        
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid character encoding"
            )
    
    def _sanitize_json_recursively(self, data: Any) -> Any:
        """Recursively sanitize JSON data structure."""
        if isinstance(data, dict):
            return {key: self._sanitize_json_recursively(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_recursively(item) for item in data]
        elif isinstance(data, str):
            # Validate string for malicious patterns
            # if self._contains_malicious_patterns(data):
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail="Potentially malicious content detected"
            #     )
            return self._sanitize_string(data, max_length=self.max_lengths['long_text'])
        else:
            return data
    
    def _sanitize_string(self, value: str, max_length: int = 1000) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return value
        
        # HTML sanitization
        sanitized = bleach.clean(
            value, 
            tags=self.allowed_tags, 
            attributes=self.allowed_attributes, 
            strip=True
        )
        
        # Length validation
        if len(sanitized) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long. Maximum {max_length} characters allowed"
            )
        
        return sanitized.strip()
    
    def _contains_malicious_patterns(self, value: str) -> bool:
        """Check if string contains potentially malicious patterns."""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt: {pattern}")
                return True
        
        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt: {pattern}")
                return True
        
        # Check for path traversal
        if '../' in value or '..\\' in value:
            logger.warning("Potential path traversal attempt")
            return True
        
        # Check for null bytes
        if '\x00' in value:
            logger.warning("Null byte detected")
            return True
        
        return False
    
    def _validate_specific_fields(self, field_name: str, value: str) -> str:
        """Apply field-specific validation rules."""
        if field_name == 'thread_id':
            if not re.match(r'^[a-zA-Z0-9_-]+$', value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Thread ID can only contain alphanumeric characters, underscores, and hyphens"
                )
            return self._sanitize_string(value, self.max_lengths['thread_id'])
        
        elif field_name == 'model':
            if not re.match(r'^[a-zA-Z0-9._-]+$', value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Model name contains invalid characters"
                )
            return self._sanitize_string(value, self.max_lengths['model_name'])
        
        elif field_name == 'provider':
            allowed_providers = ['openai', 'ollama', 'anthropic', 'google']
            if value.lower() not in allowed_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider. Must be one of: {', '.join(allowed_providers)}"
                )
            return value.lower()
        
        elif field_name == 'prompt':
            return self._sanitize_string(value, self.max_lengths['long_text'])
        
        elif field_name in ['email', 'username']:
            return self._sanitize_string(value, self.max_lengths['short_text'])
        
        else:
            return self._sanitize_string(value, self.max_lengths['medium_text'])


def create_sanitization_middleware(settings: AppSettings = None):
    """Factory function to create sanitization middleware."""
    return InputSanitizationMiddleware(settings=settings)