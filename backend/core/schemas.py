"""
Pydantic schemas for API request/response models.
"""
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from config.settings import get_settings
from core.models import ModelProvider
from core.validation import validate_thread_id, sanitize_string

settings = get_settings()


class ChatRequest(BaseModel):
    """Request model for chat endpoints."""

    thread_id: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1, max_length=10000)

    # Document upload fields
    document_filename: Optional[str] = Field(None, max_length=255)
    document_content: Optional[str] = Field(None, max_length=100000)  # Base64 encoded or text

    # Optional configuration parameters for first-time setup
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[ModelProvider] = None
    api_key: Optional[str] = Field(None, max_length=500)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    toolkits: Optional[List[str]] = Field(default_factory=list)
    enable_memory: bool = Field(default=True)

    @field_validator('thread_id')
    def validate_thread_id_format(cls, v):
        return validate_thread_id(v)

    @field_validator('prompt')
    def validate_prompt(cls, v):
        return sanitize_string(v, settings.max_prompt_length)


class ThreadStatusResponse(BaseModel):
    """Response model for thread status endpoint."""

    thread_id: str
    status: str
    configuration: dict
    usage_stats: dict


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    timestamp: str
    version: str
    active_threads: int
