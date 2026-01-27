"""
Application configuration management using Pydantic Settings.
Provides environment-specific configurations and validation.
"""

import os
import re
import json
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite:///./data/dev.db",
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

    model_config = {
        "env_prefix": "DB_",
        "env_file": ".env.development",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


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
    reset_token_expire_hours: int = Field(
        default=6,
        description="Password reset token expiration time in hours"
    )
    max_reset_attempts_per_hour: int = Field(
        default=5,
        description="Maximum password reset attempts per hour per user"
    )

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key meets basic security requirements."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters for security")
        return v
    
    model_config = {
        "env_prefix": "SECURITY_",
        "env_file": ".env.development",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


class EmailSettings(BaseSettings):
    """Email configuration settings for password reset and notifications."""
    
    # SMTP Settings
    smtp_server: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port (587 for TLS, 465 for SSL)"
    )
    smtp_username: str = Field(
        default="",
        description="SMTP username/email"
    )
    smtp_password: str = Field(
        default="",
        description="SMTP password or app password"
    )
    use_tls: bool = Field(
        default=True,
        description="Use TLS encryption (STARTTLS)"
    )
    use_ssl: bool = Field(
        default=False,
        description="Use SSL encryption"
    )
    
    # Email Content Settings
    from_email: str = Field(
        default="noreply@localai.app",
        description="From email address for password reset emails"
    )
    from_name: str = Field(
        default="LocalAI",
        description="From name for password reset emails"
    )
    
    # Email Template Settings
    base_url: str = Field(
        default="http://localhost:4321",
        description="Base URL for password reset links"
    )
    
    model_config = {
        "env_prefix": "EMAIL_",
        "env_file": ".env.development",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


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

    model_config = {
        "env_prefix": "RATE_LIMIT_",
        "env_file": ".env.development",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


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

    model_config = {
        "env_prefix": "OLLAMA_",
        "env_file": ".env.development",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


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
    default_toolkits: str = Field(
        default="Gmail,Slack,Calendar,Drive",
        description="Default available toolkits (comma-separated)"
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

    # Models configuration file path
    models_config_file: Path = Field(
        default=Path("config/models_config.json"),
        description="Path to the models configuration JSON file"
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
    email_config: EmailSettings = Field(default_factory=EmailSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins
    
    @property
    def default_toolkits_list(self) -> List[str]:
        """Get default toolkits as a list."""
        if isinstance(self.default_toolkits, str):
            return [toolkit.strip() for toolkit in self.default_toolkits.split(",") if toolkit.strip()]
        return self.default_toolkits

    @property
    def models_config(self) -> Dict[str, Any]:
        """Load and return the models configuration from JSON file."""
        return _load_models_config(self.models_config_file)

    def get_provider_models(self, provider: str) -> List[Dict[str, str]]:
        """Get models for a specific provider with title and model ID."""
        config = self.models_config
        provider_config = config.get("providers", {}).get(provider, {})
        return provider_config.get("models", [])

    def get_provider_model_ids(self, provider: str) -> List[str]:
        """Get just the model IDs for a specific provider."""
        models = self.get_provider_models(provider)
        return [m["model"] for m in models]

    @property
    def openai_models_list(self) -> List[str]:
        """Get OpenAI model IDs as a list."""
        return self.get_provider_model_ids("openai")

    @property
    def anthropic_models_list(self) -> List[str]:
        """Get Anthropic model IDs as a list."""
        return self.get_provider_model_ids("anthropic")

    @property
    def google_models_list(self) -> List[str]:
        """Get Google model IDs as a list."""
        return self.get_provider_model_ids("google")
    
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
    
    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v, info):
        """Validate CORS origins for security."""
        import os
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        
        # In production, warn about wildcard origins
        if environment == 'production':
            if '*' in v or 'localhost' in v.lower():
                raise ValueError("Production environment should not allow wildcard (*) or localhost CORS origins")
        
        # Validate each origin format
        for origin in origins:
            if origin != '*' and not re.match(r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?$', origin):
                raise ValueError(f"Invalid CORS origin format: {origin}")
        
        return v
    
    @field_validator('debug')
    @classmethod
    def validate_debug_mode(cls, v, info):
        """Validate debug mode setting."""
        import os
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        # Debug should be disabled in production
        if environment == 'production' and v is True:
            raise ValueError("Debug mode must be disabled in production environment")
        
        return v
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v, info):
        """Validate host binding."""
        import os
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        # In production, consider security implications of 0.0.0.0
        if environment == 'production' and v == '0.0.0.0':
            import warnings
            warnings.warn("Binding to 0.0.0.0 in production may expose the service. Consider using specific interfaces.")
        
        return v

    model_config = {
        "env_file": ".env.development",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore unknown environment variables
    }


@lru_cache(maxsize=1)
def _load_models_config(config_path: Path) -> Dict[str, Any]:
    """Load models configuration from JSON file with caching."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default empty config if file doesn't exist
        return {"providers": {}}
    except json.JSONDecodeError:
        # Return default empty config if JSON is invalid
        return {"providers": {}}


# Global settings instance
def get_settings() -> AppSettings:
    """Get application settings instance."""
    return AppSettings()