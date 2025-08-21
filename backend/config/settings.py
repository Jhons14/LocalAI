"""
Application configuration management using Pydantic Settings.
Provides environment-specific configurations and validation.
"""

import os
from typing import List, Optional, Dict
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
        default="dev-secret-key-change-me-in-production-please",
        description="Secret key for JWT tokens - MUST be changed in production"
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

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if v in ["your-secret-key-change-in-production", "dev-secret-key-change-me-in-production-please"]:
            raise ValueError("Secret key must be changed from default value for security")
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters for security")
        return v
    
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
    cors_origins: str = Field(
        default="http://localhost:4321,http://localhost:3000,http://localhost:4322",
        description="Allowed CORS origins (comma-separated)"
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
    
    # Tool Management
    arcade_api_key: Optional[str] = Field(
        default=None,
        description="Arcade API key for tool integration"
    )
    default_toolkits: List[str] = Field(
        default=["Gmail", "Slack", "Calendar", "Drive"],
        description="Default available toolkits"
    )
    max_tool_calls_per_turn: int = Field(
        default=5,
        description="Maximum tool calls per conversation turn"
    )
    max_recursion_depth: int = Field(
        default=25,
        description="Maximum recursion depth for tool calls"
    )
    
    # Model defaults (moved from provider-specific to general)
    default_temperature: float = Field(
        default=0.7,
        description="Default temperature for model responses"
    )
    default_max_tokens: int = Field(
        default=4000,
        description="Default maximum tokens per response"
    )
    default_timeout: int = Field(
        default=30,
        description="Default timeout for API calls in seconds"
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
    preferences_file: Path = Field(
        default=Path("user_preferences.json"),
        description="User preferences file path"
    )
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins
    
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
    
    @property
    def tool_capabilities(self) -> Dict[str, str]:
        """Tool capability descriptions."""
        return {
            "Gmail": "📧 Read, send, and manage emails",
            "Slack": "💬 Send messages and communicate in channels", 
            "Calendar": "📅 View and manage calendar events",
            "Drive": "📁 Access and manage files and documents"
        }
    
    @property
    def tool_conflicts(self) -> Dict[str, Dict]:
        """Tool conflict detection mapping."""
        return {
            "Gmail": {"conflicts_with": [], "note": ""},
            "Slack": {"conflicts_with": [], "note": ""},
            "Calendar": {"conflicts_with": [], "note": ""},
            "Drive": {"conflicts_with": [], "note": ""},
            # Example future tools that might conflict
            "Outlook": {"conflicts_with": ["Gmail"], "note": "both provide email functionality"},
            "Teams": {"conflicts_with": ["Slack"], "note": "both provide messaging functionality"},
            "OneDrive": {"conflicts_with": ["Drive"], "note": "both provide file storage"}
        }
    
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