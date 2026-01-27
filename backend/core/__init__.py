"""
Core module exports for LocalAI backend.

This module provides the core building blocks for the chat application:
- Model providers and factory for creating LLM instances
- Workflow management and building utilities
- API schemas for request/response validation
- Input validation and sanitization
- Message serialization
- Routing logic for workflows
- Tool-related utilities
"""

from core.models import ModelProvider, ModelFactory
from core.workflow import WorkflowManager, WorkflowBuilder
from core.schemas import ChatRequest, ThreadStatusResponse, HealthResponse
from core.validation import sanitize_string, validate_thread_id
from core.serialization import serialize_message
from core.routing import create_routing_function
from core.tools import create_tool_change_system_message, detect_tool_conflicts

__all__ = [
    # Models
    "ModelProvider",
    "ModelFactory",
    # Workflow
    "WorkflowManager",
    "WorkflowBuilder",
    # Schemas
    "ChatRequest",
    "ThreadStatusResponse",
    "HealthResponse",
    # Validation
    "sanitize_string",
    "validate_thread_id",
    # Serialization
    "serialize_message",
    # Routing
    "create_routing_function",
    # Tools
    "create_tool_change_system_message",
    "detect_tool_conflicts",
]
