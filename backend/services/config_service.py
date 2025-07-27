"""
Configuration service for managing API keys and application settings.
Provides secure storage and retrieval of configuration data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from cryptography.fernet import Fernet
from config.settings import AppSettings

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing configuration and API keys."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.config_path = settings.config_dir / "keys.json"
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
        
        # Ensure config directory exists
        settings.ensure_directories()
    
    def _get_or_create_encryption_key(self) -> Optional[bytes]:
        """Get or create encryption key for API key storage."""
        if self.settings.security.api_key_encryption_key:
            return self.settings.security.api_key_encryption_key.encode()
        
        key_path = self.settings.config_dir / "encryption.key"
        
        if key_path.exists():
            return key_path.read_bytes()
        
        # Generate new key in development
        if self.settings.is_development:
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            logger.info("Generated new encryption key for development")
            return key
        
        # In production, require explicit key
        logger.warning("No encryption key configured - API keys will be stored in plain text")
        return None
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a value if encryption is available."""
        if self.cipher:
            return self.cipher.encrypt(value.encode()).decode()
        return value
    
    def _decrypt_value(self, value: str) -> str:
        """Decrypt a value if encryption is available."""
        if self.cipher:
            try:
                return self.cipher.decrypt(value.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt value: {e}")
                return value
        return value
    
    def load_keys(self) -> Dict[str, Dict[str, str]]:
        """Load API keys from storage."""
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, "r") as f:
                encrypted_data = json.load(f)
            
            # Decrypt values if encryption is enabled
            if self.cipher:
                decrypted_data = {}
                for provider, models in encrypted_data.items():
                    decrypted_data[provider] = {
                        model: self._decrypt_value(api_key)
                        for model, api_key in models.items()
                    }
                return decrypted_data
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            return {}
    
    def save_keys(self, data: Dict[str, Dict[str, str]]) -> None:
        """Save API keys to storage."""
        try:
            # Encrypt values if encryption is enabled
            if self.cipher:
                encrypted_data = {}
                for provider, models in data.items():
                    encrypted_data[provider] = {
                        model: self._encrypt_value(api_key)
                        for model, api_key in models.items()
                    }
            else:
                encrypted_data = data
            
            with open(self.config_path, "w") as f:
                json.dump(encrypted_data, f, indent=2)
                
            logger.info("API keys saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
    
    def add_key(self, provider: str, model: str, api_key: str) -> None:
        """Add or update an API key."""
        data = self.load_keys()
        
        if provider not in data:
            data[provider] = {}
        
        data[provider][model] = api_key
        self.save_keys(data)
        
        logger.info(f"Added API key for {provider}/{model}")
    
    def delete_key(self, provider: str, model: str) -> bool:
        """Delete an API key."""
        data = self.load_keys()
        
        if provider in data and model in data[provider]:
            del data[provider][model]
            
            # Remove provider if no models left
            if not data[provider]:
                del data[provider]
            
            self.save_keys(data)
            logger.info(f"Deleted API key for {provider}/{model}")
            return True
        
        return False
    
    def get_key(self, provider: str, model: str) -> Optional[str]:
        """Get a specific API key."""
        data = self.load_keys()
        return data.get(provider, {}).get(model)
    
    def list_keys(self) -> Dict[str, List[str]]:
        """List available API keys without exposing the actual keys."""
        data = self.load_keys()
        return {
            provider: list(models.keys())
            for provider, models in data.items()
        }
    
    def validate_provider(self, provider: str) -> bool:
        """Validate if provider is supported."""
        supported_providers = ['openai', 'ollama']
        return provider in supported_providers