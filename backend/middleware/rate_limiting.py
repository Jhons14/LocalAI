"""
Advanced rate limiting middleware with user-based exemptions and sliding windows.
Provides sophisticated rate limiting with multiple strategies and monitoring.
"""

import time
import logging
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from config.settings import settings
from auth.dependencies import get_optional_user

logger = logging.getLogger(__name__)


class SlidingWindowRateLimit:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Rate limiting key (usually IP or user ID)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Clean old requests outside the window
        request_times = self.requests[key]
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Calculate rate limit info
        requests_in_window = len(request_times)
        remaining = max(0, self.max_requests - requests_in_window)
        
        rate_limit_info = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset_time": int(window_start + self.window_seconds),
            "window_seconds": self.window_seconds
        }
        
        # Check if request is allowed
        if requests_in_window >= self.max_requests:
            return False, rate_limit_info
        
        # Add current request to window
        request_times.append(current_time)
        rate_limit_info["remaining"] = remaining - 1
        
        return True, rate_limit_info


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with user authentication awareness."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Initialize rate limiters for different endpoint types
        self.limiters = {
            "auth": SlidingWindowRateLimit(
                max_requests=10,  # 10 requests per 5 minutes for auth endpoints
                window_seconds=300
            ),
            "chat": SlidingWindowRateLimit(
                max_requests=settings.rate_limit.chat_requests_per_minute,
                window_seconds=60
            ),
            "api_keys": SlidingWindowRateLimit(
                max_requests=settings.rate_limit.key_operations_per_minute,
                window_seconds=60
            ),
            "default": SlidingWindowRateLimit(
                max_requests=60,  # General rate limit
                window_seconds=60
            )
        }
        
        # Track suspicious activity
        self.suspicious_activity: Dict[str, dict] = defaultdict(lambda: {
            "failed_requests": deque(),
            "rapid_requests": 0,
            "last_request_time": 0
        })
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Determine rate limit category
        rate_limit_category = self._get_rate_limit_category(request)
        
        # Check for authenticated user exemptions
        is_exempt, exemption_reason = await self._check_exemptions(request)
        
        if not is_exempt:
            # Apply rate limiting
            is_allowed, rate_info = self._check_rate_limit(
                client_id, rate_limit_category, request
            )
            
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded: {client_id} "
                    f"for {rate_limit_category} from {self._get_client_ip(request)}"
                )
                
                # Return rate limit error with headers
                return self._create_rate_limit_response(rate_info)
        else:
            # Create dummy rate info for exempt users
            rate_info = {
                "limit": "unlimited",
                "remaining": "unlimited",
                "reset_time": int(time.time() + 3600),
                "exempt": True,
                "reason": exemption_reason
            }
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add rate limit headers to response
            self._add_rate_limit_headers(response, rate_info)
            
            return response
            
        except Exception as e:
            # Track failed requests for suspicious activity detection
            self._track_failed_request(client_id, str(e))
            raise
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get user ID from token if available
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from auth.jwt_handler import JWTHandler
                jwt_handler = JWTHandler(settings)
                token = auth_header.split(" ")[1]
                payload = jwt_handler.verify_token(token)
                if payload:
                    return f"user:{payload.get('sub')}"
            except Exception:
                pass  # Fall back to IP-based limiting
        
        # Fall back to IP address
        return f"ip:{self._get_client_ip(request)}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_rate_limit_category(self, request: Request) -> str:
        """Determine rate limit category based on request path."""
        path = request.url.path.lower()
        
        # Authentication endpoints
        if path.startswith("/auth/"):
            return "auth"
        
        # Chat endpoints
        if "/chat" in path or "/configure" in path:
            return "chat"
        
        # API key management
        if "/keys" in path or "api-key" in path:
            return "api_keys"
        
        # Default category
        return "default"
    
    async def _check_exemptions(self, request: Request) -> tuple[bool, Optional[str]]:
        """Check if request should be exempt from rate limiting."""
        
        # Health check endpoints are always exempt
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return True, "system_endpoint"
        
        # Check for authenticated admin users
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from auth.jwt_handler import JWTHandler
                jwt_handler = JWTHandler(settings)
                token = auth_header.split(" ")[1]
                payload = jwt_handler.verify_token(token)
                
                if payload and payload.get("is_admin"):
                    return True, "admin_user"
                
                if payload:
                    return True, "authenticated_user"
                    
        except Exception:
            pass
        
        return False, None
    
    def _check_rate_limit(
        self, 
        client_id: str, 
        category: str, 
        request: Request
    ) -> tuple[bool, dict]:
        """Check if request passes rate limiting."""
        
        # Get appropriate limiter
        limiter = self.limiters.get(category, self.limiters["default"])
        
        # Apply rate limiting
        is_allowed, rate_info = limiter.is_allowed(client_id)
        
        # Track suspicious activity
        self._track_request_pattern(client_id, is_allowed)
        
        # Add category to rate info
        rate_info["category"] = category
        rate_info["client_id"] = client_id
        
        return is_allowed, rate_info
    
    def _track_request_pattern(self, client_id: str, is_allowed: bool):
        """Track request patterns for suspicious activity detection."""
        current_time = time.time()
        activity = self.suspicious_activity[client_id]
        
        # Check for rapid requests (more than 10 per second)
        if current_time - activity["last_request_time"] < 0.1:
            activity["rapid_requests"] += 1
            if activity["rapid_requests"] > 50:  # Potential bot/attack
                logger.warning(f"Rapid request pattern detected: {client_id}")
        else:
            activity["rapid_requests"] = 0
        
        activity["last_request_time"] = current_time
        
        # Track failed rate limit attempts
        if not is_allowed:
            activity["failed_requests"].append(current_time)
            
            # Clean old failed requests (last 5 minutes)
            cutoff = current_time - 300
            while (activity["failed_requests"] and 
                   activity["failed_requests"][0] < cutoff):
                activity["failed_requests"].popleft()
            
            # If too many failed requests, it might be an attack
            if len(activity["failed_requests"]) > 20:
                logger.error(f"Potential rate limit attack: {client_id}")
    
    def _track_failed_request(self, client_id: str, error: str):
        """Track failed requests for security monitoring."""
        logger.debug(f"Failed request tracked: {client_id} - {error}")
        # In a production system, you'd send this to a security monitoring system
    
    def _add_rate_limit_headers(self, response: Response, rate_info: dict):
        """Add rate limiting information to response headers."""
        if rate_info.get("exempt"):
            response.headers["X-RateLimit-Exempt"] = "true"
            response.headers["X-RateLimit-Reason"] = rate_info.get("reason", "unknown")
        else:
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
            response.headers["X-RateLimit-Category"] = rate_info.get("category", "default")
    
    def _create_rate_limit_response(self, rate_info: dict) -> Response:
        """Create rate limit exceeded response."""
        from fastapi.responses import JSONResponse
        
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": {
                        "limit": rate_info["limit"],
                        "window_seconds": rate_info["window_seconds"],
                        "reset_time": rate_info["reset_time"],
                        "category": rate_info.get("category", "default")
                    }
                }
            }
        )
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, rate_info)
        
        return response