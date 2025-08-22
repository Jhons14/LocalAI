"""
SQLAlchemy database models for the LocalAI application.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(Base, TimestampMixin):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Rate limiting fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until


class APIKey(Base, TimestampMixin):
    """API key storage model with encryption support."""
    
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'openai', 'ollama', etc.
    model_name = Column(String(100), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    name = Column(String(100), nullable=True)  # User-friendly name
    description = Column(Text, nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index("idx_api_keys_user_provider_model", "user_id", "provider", "model_name"),
        Index("idx_api_keys_provider_active", "provider", "is_active"),
    )
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, provider={self.provider}, model={self.model_name})>"


class ChatSession(Base, TimestampMixin):
    """Chat session model to group related messages."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Anonymous sessions allowed
    thread_id = Column(String(100), nullable=False, index=True)  # External thread identifier
    
    # Session metadata
    title = Column(String(200), nullable=True)  # User-defined title
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Session statistics
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_chat_sessions_user_active", "user_id", "is_active"),
        Index("idx_chat_sessions_thread_unique", "thread_id"),
        Index("idx_chat_sessions_activity", "last_activity"),
    )
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, thread_id={self.thread_id}, provider={self.provider})>"


class ChatMessage(Base, TimestampMixin):
    """Individual chat message model."""
    
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Message metadata
    token_count = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Error handling
    is_error = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_chat_messages_session_created", "session_id", "created_at"),
        Index("idx_chat_messages_role", "role"),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
    
    @property
    def content_preview(self) -> str:
        """Get a preview of the message content (first 100 characters)."""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."