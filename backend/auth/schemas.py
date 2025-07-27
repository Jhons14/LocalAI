"""
Pydantic schemas for authentication and user management.
Defines request/response models for auth endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime


class Token(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data model."""
    user_id: Optional[str] = Field(None, description="User ID from token")
    email: Optional[str] = Field(None, description="User email from token")
    scopes: list[str] = Field(default_factory=list, description="User permissions/scopes")


class UserCreate(BaseModel):
    """User registration request model."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    full_name: Optional[str] = Field(None, max_length=200, description="User full name")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        # Username validation rules
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        if v.lower() in ['admin', 'root', 'system', 'api', 'null', 'undefined']:
            raise ValueError('Username is reserved')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Basic password validation (detailed validation in PasswordHandler)
        if len(v.strip()) != len(v):
            raise ValueError('Password cannot start or end with whitespace')
        return v


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Extended session duration")


class UserResponse(BaseModel):
    """User information response model."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="User full name")
    is_active: bool = Field(..., description="Whether user account is active")
    is_admin: bool = Field(..., description="Whether user has admin privileges")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """User profile update request model."""
    full_name: Optional[str] = Field(None, max_length=200, description="User full name")
    email: Optional[EmailStr] = Field(None, description="New email address")
    current_password: Optional[str] = Field(None, description="Current password for verification")
    new_password: Optional[str] = Field(None, min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v is not None:
            if len(v.strip()) != len(v):
                raise ValueError('Password cannot start or end with whitespace')
        return v


class PasswordReset(BaseModel):
    """Password reset request model."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v.strip()) != len(v):
            raise ValueError('Password cannot start or end with whitespace')
        return v


class RefreshToken(BaseModel):
    """Refresh token request model."""
    refresh_token: str = Field(..., description="JWT refresh token")


class UserStats(BaseModel):
    """User statistics response model."""
    total_chat_sessions: int = Field(..., description="Total chat sessions")
    total_messages: int = Field(..., description="Total messages sent")
    api_keys_count: int = Field(..., description="Number of configured API keys")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    account_age_days: int = Field(..., description="Account age in days")


class SecurityEvent(BaseModel):
    """Security event model for logging."""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[str] = Field(None, description="User ID involved")
    ip_address: str = Field(..., description="Source IP address")
    user_agent: str = Field(..., description="User agent string")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    details: Optional[dict] = Field(None, description="Additional event details")
    severity: str = Field(default="info", description="Event severity level")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        valid_severities = ['info', 'warning', 'error', 'critical']
        if v not in valid_severities:
            raise ValueError(f'Severity must be one of: {", ".join(valid_severities)}')
        return v


class APIKeyCreate(BaseModel):
    """API key creation request model."""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    provider: str = Field(..., description="Provider (openai, ollama)")
    model_name: str = Field(..., description="Model name")
    api_key: str = Field(..., min_length=10, max_length=500, description="API key value")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'ollama']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v


class APIKeyResponse(BaseModel):
    """API key response model (without exposing the actual key)."""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    provider: str = Field(..., description="Provider")
    model_name: str = Field(..., description="Model name")
    description: Optional[str] = Field(None, description="API key description")
    is_active: bool = Field(..., description="Whether API key is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last used timestamp")
    usage_count: int = Field(..., description="Usage count")
    
    model_config = {"from_attributes": True}