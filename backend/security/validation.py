"""
Security validation utilities for input sanitization and validation.
Provides comprehensive input validation and sanitization functions.
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import bleach
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Comprehensive security validation utilities."""
    
    # Allowed HTML tags and attributes for rich text content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote',
        'code', 'pre', 'a'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }
    
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    # Common injection patterns
    INJECTION_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'expression\s*\(',  # CSS expressions
        r'@import',  # CSS imports
        r'data:text/html',  # Data URLs with HTML
        r'vbscript:',  # VBScript URLs
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)',
        r'[\'"]\s*(OR|AND)\s*[\'"]\s*=\s*[\'"]',
        r';\s*(DROP|DELETE|INSERT|UPDATE)',
    ]
    
    def __init__(self):
        self.bleach_cleaner = bleach.Cleaner(
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            protocols=self.ALLOWED_PROTOCOLS,
            strip=True
        )
    
    def sanitize_html(self, content: str) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.
        
        Args:
            content: Raw HTML content to sanitize
            
        Returns:
            Sanitized HTML content
        """
        if not content:
            return ""
        
        # First pass: remove dangerous patterns
        for pattern in self.INJECTION_PATTERNS:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Second pass: use bleach for proper HTML sanitization
        sanitized = self.bleach_cleaner.clean(content)
        
        return sanitized
    
    def sanitize_text(self, text: str, max_length: int = 10000) -> str:
        """
        Sanitize plain text input.
        
        Args:
            text: Raw text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
            
        Raises:
            ValueError: If text is too long or contains dangerous patterns
        """
        if not text:
            return ""
        
        # Check length
        if len(text) > max_length:
            raise ValueError(f"Text too long. Maximum {max_length} characters allowed")
        
        # HTML escape for safety
        sanitized = html.escape(text, quote=True)
        
        # Remove control characters except common whitespace
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Check for injection patterns
        if self._contains_injection_patterns(sanitized):
            logger.warning(f"Potential injection attempt detected in text input")
            raise ValueError("Input contains potentially dangerous content")
        
        return sanitized.strip()
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email address format and security.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid and safe
        """
        if not email or len(email) > 254:  # RFC 5321 limit
            return False
        
        # Basic email regex (RFC 5322 compliant)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False
        
        # Check for dangerous patterns
        if self._contains_injection_patterns(email):
            return False
        
        # Additional security checks
        local_part, domain = email.split('@', 1)
        
        # Local part checks
        if len(local_part) > 64:  # RFC 5321 limit
            return False
        
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        
        if '..' in local_part:
            return False
        
        # Domain checks
        if len(domain) > 253:
            return False
        
        # Check for suspicious domains
        suspicious_domains = [
            'tempmail', 'disposable', '10minute', 'guerrilla',
            'mailinator', 'discard'
        ]
        
        domain_lower = domain.lower()
        for suspicious in suspicious_domains:
            if suspicious in domain_lower:
                logger.warning(f"Potentially disposable email domain: {domain}")
        
        return True
    
    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> bool:
        """
        Validate URL for security and format.
        
        Args:
            url: URL to validate
            allowed_schemes: List of allowed URL schemes (default: http, https)
            
        Returns:
            True if URL is valid and safe
        """
        if not url:
            return False
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme.lower() not in allowed_schemes:
                return False
            
            # Check for dangerous patterns
            if self._contains_injection_patterns(url):
                return False
            
            # Check for localhost/private IPs in production
            if hasattr(self, 'settings') and self.settings.is_production:
                hostname = parsed.hostname
                if hostname:
                    if (hostname in ['localhost', '127.0.0.1'] or
                        hostname.startswith('192.168.') or
                        hostname.startswith('10.') or
                        hostname.startswith('172.')):
                        return False
            
            return True
            
        except Exception:
            return False
    
    def validate_filename(self, filename: str) -> bool:
        """
        Validate filename for security.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if filename is safe
        """
        if not filename:
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # Check for reserved names (Windows)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False
        
        # Check for executable extensions
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
            '.vbs', '.js', '.jar', '.ps1', '.sh'
        ]
        
        file_extension = Path(filename).suffix.lower()
        if file_extension in dangerous_extensions:
            return False
        
        return True
    
    def validate_thread_id(self, thread_id: str) -> bool:
        """
        Validate thread ID format for security.
        
        Args:
            thread_id: Thread ID to validate
            
        Returns:
            True if thread ID is valid
        """
        if not thread_id:
            return False
        
        # Length check
        if len(thread_id) > 100:
            return False
        
        # Pattern check: alphanumeric, underscores, hyphens only
        if not re.match(r'^[a-zA-Z0-9_-]+$', thread_id):
            return False
        
        return True
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if API key format is valid
        """
        if not api_key:
            return False
        
        # Length check (most API keys are between 20-200 characters)
        if len(api_key) < 10 or len(api_key) > 500:
            return False
        
        # Check for obviously fake keys
        fake_patterns = [
            r'^(test|fake|demo|sample)',
            r'^sk-[0-9]+$',  # Obviously fake OpenAI key
            r'^[a-zA-Z]+$',  # Only letters
            r'^[0-9]+$',     # Only numbers
        ]
        
        for pattern in fake_patterns:
            if re.match(pattern, api_key, re.IGNORECASE):
                return False
        
        return True
    
    def _contains_injection_patterns(self, text: str) -> bool:
        """Check if text contains injection patterns."""
        text_lower = text.lower()
        
        # Check XSS patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Check SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False


# Convenience functions
def sanitize_input(
    value: Any,
    input_type: str = "text",
    max_length: int = 10000,
    **kwargs
) -> Any:
    """
    Sanitize input based on type.
    
    Args:
        value: Value to sanitize
        input_type: Type of input ('text', 'html', 'email', 'url', etc.)
        max_length: Maximum length for text inputs
        **kwargs: Additional parameters for specific validators
        
    Returns:
        Sanitized value
        
    Raises:
        ValueError: If validation fails
    """
    if value is None:
        return None
    
    validator = SecurityValidator()
    
    if input_type == "text":
        return validator.sanitize_text(str(value), max_length)
    elif input_type == "html":
        return validator.sanitize_html(str(value))
    elif input_type == "email":
        email = str(value).strip().lower()
        if not validator.validate_email(email):
            raise ValueError("Invalid email address")
        return email
    elif input_type == "url":
        url = str(value).strip()
        if not validator.validate_url(url, kwargs.get('allowed_schemes')):
            raise ValueError("Invalid URL")
        return url
    elif input_type == "filename":
        filename = str(value).strip()
        if not validator.validate_filename(filename):
            raise ValueError("Invalid filename")
        return filename
    elif input_type == "thread_id":
        thread_id = str(value).strip()
        if not validator.validate_thread_id(thread_id):
            raise ValueError("Invalid thread ID")
        return thread_id
    elif input_type == "api_key":
        api_key = str(value).strip()
        if not validator.validate_api_key(api_key):
            raise ValueError("Invalid API key format")
        return api_key
    else:
        # Default to text sanitization
        return validator.sanitize_text(str(value), max_length)


def validate_file_upload(
    filename: str,
    content: bytes,
    max_size: int = 10 * 1024 * 1024,  # 10MB default
    allowed_types: List[str] = None
) -> Dict[str, Any]:
    """
    Validate file upload for security.
    
    Args:
        filename: Original filename
        content: File content bytes
        max_size: Maximum file size in bytes
        allowed_types: List of allowed MIME types
        
    Returns:
        Validation result dictionary
        
    Raises:
        ValueError: If file validation fails
    """
    validator = SecurityValidator()
    
    # Validate filename
    if not validator.validate_filename(filename):
        raise ValueError("Invalid or dangerous filename")
    
    # Check file size
    if len(content) > max_size:
        raise ValueError(f"File too large. Maximum size: {max_size} bytes")
    
    # Check file content for malicious patterns
    content_str = content[:1024].decode('utf-8', errors='ignore')  # Check first 1KB
    if validator._contains_injection_patterns(content_str):
        raise ValueError("File contains potentially malicious content")
    
    # Additional MIME type validation would go here
    # This would require python-magic library for proper detection
    
    return {
        "filename": filename,
        "size": len(content),
        "is_safe": True
    }