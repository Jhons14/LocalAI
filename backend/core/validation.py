"""
Input validation and sanitization utilities.
"""
import re
import bleach

from config.settings import get_settings

settings = get_settings()


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize and validate string input.

    Args:
        value: The input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is not a string or exceeds max length
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    sanitized = bleach.clean(value, tags=[], attributes={}, strip=True)

    if len(sanitized) > max_length:
        raise ValueError(f"Input too long. Maximum {max_length} characters allowed")

    return sanitized.strip()


def validate_thread_id(thread_id: str) -> str:
    """
    Validate thread ID format.

    Args:
        thread_id: The thread ID to validate

    Returns:
        Validated thread ID

    Raises:
        ValueError: If thread ID format is invalid or too long
    """
    if not re.match(r'^[a-zA-Z0-9_-]+$', thread_id):
        raise ValueError("Thread ID can only contain alphanumeric characters, underscores, and hyphens")

    if len(thread_id) > settings.max_thread_id_length:
        raise ValueError(f"Thread ID too long. Maximum {settings.max_thread_id_length} characters allowed")

    return thread_id
