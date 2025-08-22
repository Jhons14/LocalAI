"""
User-based rate limiting service.
"""

import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import HTTPException, status
from config.settings import AppSettings


class UserRateLimiter:
    """Rate limiter that tracks usage per user ID."""
    
    def __init__(self, settings: AppSettings):
        """Initialize rate limiter with settings."""
        self.settings = settings
        
        # Storage for rate limiting data: {user_id: {endpoint: deque_of_timestamps}}
        self._user_requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Cleanup tracking
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
    
    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory leaks."""
        current_time = time.time()
        
        # Only run cleanup every few minutes
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Remove requests older than 1 hour
        
        for user_id in list(self._user_requests.keys()):
            user_data = self._user_requests[user_id]
            
            for endpoint in list(user_data.keys()):
                request_times = user_data[endpoint]
                
                # Remove old timestamps
                while request_times and request_times[0] < cutoff_time:
                    request_times.popleft()
                
                # Remove empty endpoint entries
                if not request_times:
                    del user_data[endpoint]
            
            # Remove empty user entries
            if not user_data:
                del self._user_requests[user_id]
        
        self._last_cleanup = current_time
    
    def _get_rate_limit(self, endpoint_type: str) -> int:
        """Get rate limit for endpoint type."""
        if endpoint_type == "chat":
            return self.settings.rate_limit.chat_requests_per_minute
        elif endpoint_type == "key_operations":
            return self.settings.rate_limit.key_operations_per_minute
        elif endpoint_type == "model_requests":
            return self.settings.rate_limit.model_requests_per_minute
        else:
            return 60  # Default fallback
    
    def check_rate_limit(self, user_id: str, endpoint_type: str) -> bool:
        """
        Check if user is within rate limits for endpoint type.
        
        Args:
            user_id: User's unique identifier
            endpoint_type: Type of endpoint ("chat", "key_operations", "model_requests")
            
        Returns:
            True if within limits, False if rate limited
        """
        self._cleanup_old_requests()
        
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Get user's request history for this endpoint
        user_requests = self._user_requests[user_id][endpoint_type]
        
        # Remove requests outside the time window
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        # Check if within rate limit
        rate_limit = self._get_rate_limit(endpoint_type)
        return len(user_requests) < rate_limit
    
    def record_request(self, user_id: str, endpoint_type: str):
        """
        Record a request for rate limiting tracking.
        
        Args:
            user_id: User's unique identifier
            endpoint_type: Type of endpoint
        """
        current_time = time.time()
        self._user_requests[user_id][endpoint_type].append(current_time)
    
    def enforce_rate_limit(self, user_id: str, endpoint_type: str):
        """
        Enforce rate limit by checking and recording request.
        
        Args:
            user_id: User's unique identifier
            endpoint_type: Type of endpoint
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        if not self.check_rate_limit(user_id, endpoint_type):
            rate_limit = self._get_rate_limit(endpoint_type)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {rate_limit} requests per minute for {endpoint_type}",
                headers={"Retry-After": "60"}
            )
        
        self.record_request(user_id, endpoint_type)
    
    def get_user_stats(self, user_id: str) -> Dict[str, Dict[str, int]]:
        """
        Get current rate limit stats for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary with current usage and limits
        """
        self._cleanup_old_requests()
        
        current_time = time.time()
        window_start = current_time - 60
        
        stats = {}
        
        for endpoint_type in ["chat", "key_operations", "model_requests"]:
            user_requests = self._user_requests[user_id][endpoint_type]
            
            # Count requests in current window
            current_requests = sum(1 for req_time in user_requests if req_time >= window_start)
            rate_limit = self._get_rate_limit(endpoint_type)
            
            stats[endpoint_type] = {
                "current_requests": current_requests,
                "rate_limit": rate_limit,
                "remaining": max(0, rate_limit - current_requests)
            }
        
        return stats
    
    def reset_user_limits(self, user_id: str):
        """
        Reset rate limits for a specific user.
        
        Args:
            user_id: User's unique identifier
        """
        if user_id in self._user_requests:
            del self._user_requests[user_id]