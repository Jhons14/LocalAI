"""
Enhanced rate limiting middleware with user-specific limits and analytics.
"""

import time
import json
from typing import Dict, Optional, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from database.models import User
from .rate_limiter import UserRateLimiter
from config.settings import AppSettings
import logging

logger = logging.getLogger(__name__)


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting middleware with user-specific limits,
    analytics tracking, and flexible configuration.
    """
    
    def __init__(self, app, settings: AppSettings):
        """Initialize enhanced rate limiting middleware."""
        super().__init__(app)
        self.settings = settings
        self.rate_limiter = UserRateLimiter(settings)
        
        # Rate limiting configuration per endpoint pattern
        self.endpoint_configs = {
            "auth_login": {
                "pattern": "/auth/login",
                "limit": 5,  # 5 attempts per minute
                "window": 60,
                "message": "Too many login attempts"
            },
            "auth_register": {
                "pattern": "/auth/register", 
                "limit": 3,  # 3 registrations per minute
                "window": 60,
                "message": "Too many registration attempts"
            },
            "chat": {
                "pattern": "/chat",
                "limit": settings.rate_limit.chat_requests_per_minute,
                "window": 60,
                "message": "Chat rate limit exceeded"
            },
            "models": {
                "pattern": "/models",
                "limit": settings.rate_limit.model_requests_per_minute,
                "window": 60,
                "message": "Model requests rate limit exceeded"
            },
            "key_operations": {
                "pattern": "/auth/",
                "limit": settings.rate_limit.key_operations_per_minute,
                "window": 60,
                "message": "Authentication operations rate limit exceeded"
            }
        }
        
        # IP-based tracking for unauthenticated requests
        self.ip_requests: Dict[str, Dict[str, list]] = {}
        
        # Analytics storage
        self.analytics = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "user_stats": {},
            "endpoint_stats": {}
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_type(self, path: str, method: str) -> Optional[str]:
        """Determine endpoint type for rate limiting."""
        for endpoint_type, config in self.endpoint_configs.items():
            if config["pattern"] in path:
                return endpoint_type
        return None
    
    def _check_ip_rate_limit(self, ip: str, endpoint_type: str) -> bool:
        """Check rate limits for unauthenticated requests by IP."""
        current_time = time.time()
        
        if ip not in self.ip_requests:
            self.ip_requests[ip] = {}
        
        if endpoint_type not in self.ip_requests[ip]:
            self.ip_requests[ip][endpoint_type] = []
        
        requests = self.ip_requests[ip][endpoint_type]
        config = self.endpoint_configs.get(endpoint_type, {})
        window = config.get("window", 60)
        limit = config.get("limit", 60)
        
        # Remove old requests
        cutoff = current_time - window
        requests[:] = [req_time for req_time in requests if req_time > cutoff]
        
        # Check limit
        if len(requests) >= limit:
            return False
        
        # Record request
        requests.append(current_time)
        return True
    
    def _update_analytics(self, user_id: Optional[str], endpoint_type: str, was_rate_limited: bool):
        """Update analytics data."""
        self.analytics["total_requests"] += 1
        
        if was_rate_limited:
            self.analytics["rate_limited_requests"] += 1
        
        # User-specific analytics
        if user_id:
            if user_id not in self.analytics["user_stats"]:
                self.analytics["user_stats"][user_id] = {
                    "total_requests": 0,
                    "rate_limited": 0,
                    "endpoints": {}
                }
            
            user_stats = self.analytics["user_stats"][user_id]
            user_stats["total_requests"] += 1
            
            if was_rate_limited:
                user_stats["rate_limited"] += 1
            
            if endpoint_type not in user_stats["endpoints"]:
                user_stats["endpoints"][endpoint_type] = 0
            user_stats["endpoints"][endpoint_type] += 1
        
        # Endpoint analytics
        if endpoint_type not in self.analytics["endpoint_stats"]:
            self.analytics["endpoint_stats"][endpoint_type] = {
                "total_requests": 0,
                "rate_limited": 0
            }
        
        endpoint_stats = self.analytics["endpoint_stats"][endpoint_type]
        endpoint_stats["total_requests"] += 1
        
        if was_rate_limited:
            endpoint_stats["rate_limited"] += 1
    
    def _create_rate_limit_response(self, endpoint_type: str, reset_time: int) -> JSONResponse:
        """Create standardized rate limit response."""
        config = self.endpoint_configs.get(endpoint_type, {})
        message = config.get("message", "Rate limit exceeded")
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": message,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "endpoint_type": endpoint_type,
                "retry_after": reset_time
            },
            headers={
                "Retry-After": str(reset_time),
                "X-RateLimit-Reset": str(int(time.time()) + reset_time)
            }
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting middleware."""
        start_time = time.time()
        
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get endpoint type
        endpoint_type = self._get_endpoint_type(request.url.path, request.method)
        if not endpoint_type:
            return await call_next(request)
        
        # Get user and IP
        user: Optional[User] = getattr(request.state, "user", None)
        user_id = user.id if user else None
        client_ip = self._get_client_ip(request)
        
        rate_limited = False
        
        try:
            if user_id:
                # User-based rate limiting
                if not self.rate_limiter.check_rate_limit(user_id, endpoint_type):
                    rate_limited = True
                    self._update_analytics(user_id, endpoint_type, True)
                    return self._create_rate_limit_response(endpoint_type, 60)
                
                # Record request for analytics
                self.rate_limiter.record_request(user_id, endpoint_type)
                
            else:
                # IP-based rate limiting for unauthenticated requests
                if not self._check_ip_rate_limit(client_ip, endpoint_type):
                    rate_limited = True
                    self._update_analytics(None, endpoint_type, True)
                    return self._create_rate_limit_response(endpoint_type, 60)
            
            # Update analytics for successful requests
            self._update_analytics(user_id, endpoint_type, False)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            if user_id:
                stats = self.rate_limiter.get_user_stats(user_id)
                if endpoint_type in stats:
                    endpoint_stats = stats[endpoint_type]
                    response.headers["X-RateLimit-Limit"] = str(endpoint_stats["rate_limit"])
                    response.headers["X-RateLimit-Remaining"] = str(endpoint_stats["remaining"])
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Don't block requests on middleware errors
            return await call_next(request)
    
    def get_analytics(self) -> Dict:
        """Get current rate limiting analytics."""
        return {
            "analytics": self.analytics,
            "active_users": len(self.analytics["user_stats"]),
            "rate_limit_percentage": (
                (self.analytics["rate_limited_requests"] / max(self.analytics["total_requests"], 1)) * 100
            )
        }
    
    def reset_analytics(self):
        """Reset analytics data."""
        self.analytics = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "user_stats": {},
            "endpoint_stats": {}
        }
    
    def get_user_rate_limit_status(self, user_id: str) -> Dict:
        """Get detailed rate limit status for a specific user."""
        if user_id not in self.analytics["user_stats"]:
            return {"error": "User not found in analytics"}
        
        user_stats = self.analytics["user_stats"][user_id]
        current_limits = self.rate_limiter.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "total_requests": user_stats["total_requests"],
            "rate_limited_requests": user_stats["rate_limited"],
            "current_limits": current_limits,
            "endpoints_used": user_stats["endpoints"]
        }