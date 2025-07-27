"""
Application configuration management using Pydantic Settings.
Provides environment-specific configurations and validation.
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite:///./app.db",
        description="Database URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    pool_size: int = Field(
        default=10,
        description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=20,
        description="Maximum database connection overflow"
    )

    model_config = {"env_prefix": "DB_"}


class SecuritySettings(BaseSettings):
    """Security-related configuration settings."""
    
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    api_key_encryption_key: Optional[str] = Field(
        default=None,
        description="Key for encrypting stored API keys"
    )
    max_login_attempts: int = Field(
        default=5,
        description="Maximum login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=15,
        description="Lockout duration in minutes"
    )

    model_config = {"env_prefix": "SECURITY_"}


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration settings."""
    
    chat_requests_per_minute: int = Field(
        default=30,
        description="Chat requests per minute per IP"
    )
    key_operations_per_minute: int = Field(
        default=10,
        description="Key operations per minute per IP"
    )
    model_requests_per_minute: int = Field(
        default=20,
        description="Model requests per minute per IP"
    )

    model_config = {"env_prefix": "RATE_LIMIT_"}


class OllamaSettings(BaseSettings):
    """Ollama-specific configuration settings."""
    
    base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries"
    )

    model_config = {"env_prefix": "OLLAMA_"}


class OpenAISettings(BaseSettings):
    """OpenAI-specific configuration settings."""
    
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_tokens: int = Field(
        default=4000,
        description="Maximum tokens per request"
    )
    max_retries: int = Field(
        default=2,
        description="Maximum number of retries"
    )

    model_config = {"env_prefix": "OPENAI_"}


class AppSettings(BaseSettings):
    """Main application settings."""
    
    # Basic app settings
    app_name: str = Field(
        default="LocalAI Chat API",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    
    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:4321", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    
    # Input validation settings
    max_prompt_length: int = Field(
        default=10000,
        description="Maximum prompt length"
    )
    max_thread_id_length: int = Field(
        default=100,
        description="Maximum thread ID length"
    )
    
    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: str = Field(
        default="app.log",
        description="Log file path"
    )
    
    # Storage settings
    config_dir: Path = Field(
        default=Path("config"),
        description="Configuration directory"
    )
    data_dir: Path = Field(
        default=Path("data"),
        description="Data directory"
    )
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        valid_environments = ['development', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {", ".join(valid_environments)}')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global settings instance
def get_settings() -> AppSettings:
    """Get application settings instance."""
    return AppSettings()


# Create settings instance
settings = get_settings()