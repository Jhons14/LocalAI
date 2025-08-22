"""
Error handling middleware for structured error responses.
Provides consistent error formatting and logging.
"""

import logging
import traceback
import uuid
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from config.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and providing consistent error responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any errors that occur."""
        
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        try:
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except HTTPException as e:
            # FastAPI HTTPExceptions are handled normally
            return await self._create_error_response(
                request=request,
                status_code=e.status_code,
                error_code="HTTP_EXCEPTION",
                message=e.detail,
                correlation_id=correlation_id
            )
            
        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error [{correlation_id}]: {str(e)}")
            return await self._create_error_response(
                request=request,
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e),
                correlation_id=correlation_id
            )
            
        except PermissionError as e:
            # Permission/authorization errors
            logger.warning(f"Permission error [{correlation_id}]: {str(e)}")
            return await self._create_error_response(
                request=request,
                status_code=403,
                error_code="PERMISSION_ERROR",
                message="Access denied",
                correlation_id=correlation_id
            )
            
        except ConnectionError as e:
            # External service connection errors
            logger.error(f"Connection error [{correlation_id}]: {str(e)}")
            return await self._create_error_response(
                request=request,
                status_code=503,
                error_code="SERVICE_UNAVAILABLE",
                message="External service temporarily unavailable",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error [{correlation_id}]: {str(e)}")
            
            if settings.is_development:
                # In development, include traceback
                logger.error(f"Traceback [{correlation_id}]:\n{traceback.format_exc()}")
            
            return await self._create_error_response(
                request=request,
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred" if not settings.is_development else str(e),
                correlation_id=correlation_id,
                details=traceback.format_exc() if settings.is_development else None
            )
    
    async def _create_error_response(
        self,
        request: Request,
        status_code: int,
        error_code: str,
        message: str,
        correlation_id: str,
        details: str = None
    ) -> JSONResponse:
        """Create a standardized error response."""
        
        error_response = {
            "error": {
                "code": error_code,
                "message": message,
                "correlation_id": correlation_id,
                "timestamp": "2025-01-27T00:00:00Z",  # Would use actual timestamp
                "path": str(request.url.path),
                "method": request.method
            }
        }
        
        # Add details in development mode
        if details and settings.is_development:
            error_response["error"]["details"] = details
        
        # Add request context for debugging
        if settings.is_development:
            error_response["error"]["request_id"] = getattr(request.state, "request_id", None)
            error_response["error"]["user_agent"] = request.headers.get("user-agent")
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={"X-Correlation-ID": correlation_id}
        )