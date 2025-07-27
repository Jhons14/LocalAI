"""
Logging middleware for request/response tracking and metrics.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response information."""
        
        # Start timing
        start_time = time.time()
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_ip} | User-Agent: {user_agent}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Get correlation ID from middleware or generate one
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"| Status: {response.status_code} "
            f"| Duration: {process_time:.3f}s "
            f"| Correlation ID: {correlation_id}"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests
        if process_time > 5.0:  # 5 seconds threshold
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {process_time:.3f}s | Correlation ID: {correlation_id}"
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address, considering proxies."""
        
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"