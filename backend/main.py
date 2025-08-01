"""
LocalAI Chat API - Secure FastAPI application with authentication and authorization.
Integrates all security features, database management, and chat functionality.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Import configuration and database
from config.settings import settings
from database import create_tables, get_db
from database.models import User

# Import authentication and security
from auth.dependencies import get_current_active_user, get_optional_user
from routers.auth import router as auth_router
from routers.users import router as users_router

# Import middleware
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.security import SecurityHeadersMiddleware
from middleware.logging import LoggingMiddleware
from middleware.rate_limiting import RateLimitingMiddleware

# Import legacy endpoints (temporarily - will be secured)
from legacy_endpoints import create_legacy_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    
    # Create default admin user if none exists
    try:
        from database.session import SessionLocal
        from auth.password import PasswordHandler
        
        db = SessionLocal()
        try:
            admin_count = db.query(User).filter(User.is_admin == True).count()
            if admin_count == 0:
                password_handler = PasswordHandler()
                admin_user = User(
                    email="admin@localai.com",
                    username="admin",
                    hashed_password=password_handler.hash_password("AdminPass123!"),
                    is_active=True,
                    is_admin=True
                )
                db.add(admin_user)
                db.commit()
                logger.info("Default admin user created: admin@localai.com / AdminPass123!")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not create default admin user: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Secure chat interface for LLM models with authentication and authorization",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# Add middleware in correct order (last added = first executed)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include authentication routers
app.include_router(auth_router)
app.include_router(users_router)

# Include legacy endpoints (secured)
app.include_router(create_legacy_router())


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with system information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if not settings.is_production else "Contact administrator",
        "status": "running"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    from datetime import datetime
    
    # Basic health check
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment
    }
    
    # Database health check
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health_data["database"] = "healthy"
        db.close()
    except Exception as e:
        health_data["database"] = "unhealthy"
        health_data["database_error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    # Determine overall status
    if health_data.get("database") != "healthy":
        health_data["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=health_data)
    
    return health_data


@app.get("/security/status", tags=["Security"])
async def security_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get security status (authenticated users only)."""
    from security.monitoring import security_monitor
    
    if not current_user.is_admin:
        # Regular users get limited info
        return {
            "user_authenticated": True,
            "user_active": current_user.is_active,
            "account_created": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
    
    # Admins get full security summary
    summary = security_monitor.get_security_summary(hours=24)
    return {
        "user_authenticated": True,
        "user_role": "admin",
        "security_summary": summary
    }


@app.get("/info", tags=["System"])
async def app_info(user: User = Depends(get_optional_user)):
    """Application information endpoint."""
    info = {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "authentication_enabled": True,
        "features": [
            "JWT Authentication",
            "Role-based Authorization", 
            "Rate Limiting",
            "Security Monitoring",
            "Input Validation",
            "API Key Management",
            "Chat Sessions"
        ]
    }
    
    if user:
        info["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "authenticated": True
        }
    else:
        info["user"] = {"authenticated": False}
    
    return info


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found",
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "details": str(exc) if settings.is_development else "Contact administrator"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.workers,
        log_level=settings.log_level.lower()
    )