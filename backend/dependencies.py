"""
Dependency injection setup for FastAPI application.
Provides centralized dependency management for services and configurations.
"""

from fastapi import Depends
from config.settings import AppSettings, get_settings
from services.config_service import ConfigService

# Store config service instance
_config_service_instance = None

def get_config_service(settings: AppSettings = Depends(get_settings)) -> ConfigService:
    """Get ConfigService instance with dependency injection."""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService(settings)
    return _config_service_instance


# Convenience function to get settings as dependency
def get_app_settings() -> AppSettings:
    """Get application settings as dependency."""
    return get_settings()


# Rate limiting key function that can be injected
def get_rate_limit_key(request) -> str:
    """Get rate limiting key from request."""
    # Use forwarded IP if behind proxy, otherwise use direct IP
    forwarded_ip = request.headers.get("X-Forwarded-For")
    if forwarded_ip:
        return forwarded_ip.split(",")[0].strip()
    return request.client.host if request.client else "unknown"