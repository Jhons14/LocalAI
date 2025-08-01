"""
Legacy endpoints with authentication and security integration.
Provides backward compatibility while enforcing security measures.
"""

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status, Request, Depends
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

# LangChain imports
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import requests
import openai
from openai import AuthenticationError

# Local imports
from config.settings import settings
from database import get_db
from database.models import User, APIKey, ChatSession, ChatMessage
from auth.dependencies import get_current_active_user
from security.validation import sanitize_input
from security.monitoring import security_monitor, SecurityEvent, SecurityEventType, SeverityLevel
from services.config_service import ConfigService
from dependencies import get_config_service

logger = logging.getLogger(__name__)

# Global storage for workflows and memory (will be moved to database eventually)
workflow_store: dict[str, Any] = {}
memory_store: dict[str, MemorySaver] = {}


def create_legacy_router() -> APIRouter:
    """Create router with legacy endpoints that now require authentication."""
    
    router = APIRouter(prefix="/api", tags=["Chat & Models"])
    
    # Pydantic models for requests
    class KeyPayload(BaseModel):
        provider: str = Field(..., min_length=1, max_length=50)
        model: str = Field(..., min_length=1, max_length=100)
        api_key: str = Field(..., min_length=10, max_length=500)
        name: Optional[str] = Field(None, max_length=100, description="Friendly name for the API key")
        
        @field_validator('provider')
        @classmethod
        def validate_provider(cls, v):
            allowed_providers = ['openai', 'ollama']
            if v not in allowed_providers:
                raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
            return v
        
        @field_validator('api_key')
        @classmethod
        def validate_api_key(cls, v):
            return sanitize_input(v, "api_key", 500)
    
    class ValidateKeyPayload(BaseModel):
        apiKey: str = Field(..., min_length=10, max_length=500)
        
        @field_validator('apiKey')
        @classmethod
        def validate_api_key(cls, v):
            return sanitize_input(v, "api_key", 500)
    
    class ConfigRequest(BaseModel):
        thread_id: str = Field(..., min_length=1, max_length=100)
        model: str = Field(..., min_length=1, max_length=100)
        provider: str = Field(..., min_length=1, max_length=50)
        apiKey: Optional[str] = Field(None, max_length=500)
        
        @field_validator('thread_id')
        @classmethod
        def validate_thread_id_format(cls, v):
            return sanitize_input(v, "thread_id", 100)
        
        @field_validator('provider')
        @classmethod
        def validate_provider(cls, v):
            allowed_providers = ['openai', 'ollama']
            if v not in allowed_providers:
                raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
            return v
        
        @field_validator('apiKey')
        @classmethod
        def validate_api_key(cls, v):
            if v is not None:
                return sanitize_input(v, "api_key", 500)
            return v
    
    class ChatRequest(BaseModel):
        thread_id: str = Field(..., min_length=1, max_length=100)
        prompt: str = Field(..., min_length=1, max_length=settings.max_prompt_length)
        
        @field_validator('thread_id')
        @classmethod
        def validate_thread_id_format(cls, v):
            return sanitize_input(v, "thread_id", 100)
        
        @field_validator('prompt')
        @classmethod
        def validate_prompt(cls, v):
            return sanitize_input(v, "text", settings.max_prompt_length)
    
    # API Key Management Endpoints (Secured)
    @router.get("/keys")
    async def list_keys(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """List user's API keys (secured version)."""
        try:
            api_keys = db.query(APIKey).filter(
                APIKey.user_id == current_user.id,
                APIKey.is_active == True
            ).all()
            
            result = {}
            for key in api_keys:
                if key.provider not in result:
                    result[key.provider] = []
                result[key.provider].append({
                    "model": key.model_name,
                    "name": key.name,
                    "created_at": key.created_at.isoformat(),
                    "last_used": key.last_used.isoformat() if key.last_used else None
                })
            
            logger.info(f"API keys listed for user: {current_user.email}")
            return result
            
        except Exception as e:
            logger.error(f"Error listing keys for user {current_user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list API keys"
            )
    
    @router.post("/keys")
    async def add_key(
        payload: KeyPayload,
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
        config_service: ConfigService = Depends(get_config_service)
    ):
        """Add API key for authenticated user (secured version)."""
        try:
            # Check if key already exists for this user/provider/model
            existing_key = db.query(APIKey).filter(
                APIKey.user_id == current_user.id,
                APIKey.provider == payload.provider,
                APIKey.model_name == payload.model,
                APIKey.is_active == True
            ).first()
            
            if existing_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API key already exists for this provider and model"
                )
            
            # Create new API key record
            new_api_key = APIKey(
                user_id=current_user.id,
                provider=payload.provider,
                model_name=payload.model,
                encrypted_key=config_service._encrypt_value(payload.api_key),
                name=payload.name or f"{payload.provider}-{payload.model}",
                is_active=True
            )
            
            db.add(new_api_key)
            db.commit()
            
            # Log security event
            security_monitor.log_event(SecurityEvent(
                event_type=SecurityEventType.API_ABUSE,  # Using closest available type
                severity=SeverityLevel.LOW,
                user_id=current_user.id,
                ip_address=_get_client_ip(request),
                details={"action": "api_key_added", "provider": payload.provider, "model": payload.model}
            ))
            
            logger.info(f"API key added for user {current_user.email}: {payload.provider}/{payload.model}")
            return {"status": "saved", "id": new_api_key.id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding API key for user {current_user.email}: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save API key"
            )
    
    @router.delete("/keys/{provider}/{model}")
    async def delete_key(
        provider: str,
        model: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Delete API key for authenticated user (secured version)."""
        try:
            api_key = db.query(APIKey).filter(
                APIKey.user_id == current_user.id,
                APIKey.provider == provider,
                APIKey.model_name == model,
                APIKey.is_active == True
            ).first()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            # Soft delete
            api_key.is_active = False
            db.commit()
            
            logger.info(f"API key deleted for user {current_user.email}: {provider}/{model}")
            return {"status": "deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting API key for user {current_user.email}: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete API key"
            )
    
    @router.post('/keys/validate-keys')
    async def validate_keys(
        payload: ValidateKeyPayload,
        current_user: User = Depends(get_current_active_user)
    ):
        """Validate OpenAI API key (secured version)."""
        try:
            # Test the API key
            client = openai.OpenAI(api_key=payload.apiKey)
            models = client.models.list()
            
            logger.info(f"API key validated successfully for user: {current_user.email}")
            return {'Valid': True, 'models_count': len(models.data)}
            
        except AuthenticationError as e:
            logger.warning(f"Invalid API key provided by user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid API key: {str(e)}'
            )
        except Exception as e:
            logger.error(f"Error validating API key for user {current_user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Validation error: {str(e)}'
            )
    
    # Model Configuration Endpoint (Secured)
    @router.post("/configure")
    async def configure_model(
        config: ConfigRequest,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
        config_service: ConfigService = Depends(get_config_service)
    ):
        """Configure model for chat session (secured version)."""
        try:
            logger.info(f"Configuring model for user {current_user.email}, thread {config.thread_id}")
            
            # Get or create chat session
            chat_session = db.query(ChatSession).filter(
                ChatSession.user_id == current_user.id,
                ChatSession.thread_id == config.thread_id
            ).first()
            
            if not chat_session:
                chat_session = ChatSession(
                    user_id=current_user.id,
                    thread_id=config.thread_id,
                    provider=config.provider,
                    model_name=config.model,
                    is_active=True
                )
                db.add(chat_session)
            else:
                chat_session.provider = config.provider
                chat_session.model_name = config.model
                chat_session.is_active = True
            
            db.commit()
            
            # Get or create memory for thread
            memory = memory_store.setdefault(
                f"{current_user.id}:{config.thread_id}", 
                MemorySaver()
            )
            
            # Create model instance
            if config.provider == "openai":
                api_key = config.apiKey
                if not api_key:
                    # Try to get from stored API keys
                    stored_key = db.query(APIKey).filter(
                        APIKey.user_id == current_user.id,
                        APIKey.provider == "openai",
                        APIKey.model_name == config.model,
                        APIKey.is_active == True
                    ).first()
                    
                    if stored_key:
                        api_key = config_service._decrypt_value(stored_key.encrypted_key)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="OpenAI API key required and not found in stored keys"
                        )
                
                model = ChatOpenAI(
                    model=config.model,
                    temperature=0,
                    max_tokens=4000,
                    timeout=30,
                    max_retries=2,
                    api_key=api_key,
                )
                
            elif config.provider == "ollama":
                model = ChatOllama(
                    model=config.model,
                    streaming=True,
                    base_url=settings.ollama.base_url,
                    timeout=settings.ollama.timeout,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported provider"
                )
            
            # Create workflow
            def call_model(state: dict):
                return {"messages": model.invoke(state["messages"])}
            
            workflow = StateGraph(state_schema=MessagesState)
            workflow.add_node("model", call_model)
            workflow.add_edge(START, "model")
            workflow_app = workflow.compile(checkpointer=memory)
            
            # Store workflow with user-specific key
            workflow_store[f"{current_user.id}:{config.thread_id}"] = workflow_app
            
            logger.info(f"Model configured successfully for user {current_user.email}")
            return {"message": f"Model configured for thread {config.thread_id}"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error configuring model for user {current_user.email}: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to configure model"
            )
    
    # Ollama Models Endpoint (Secured)
    @router.get("/getModels")
    async def get_ollama_models(
        current_user: User = Depends(get_current_active_user)
    ):
        """Get available Ollama models (secured version)."""
        try:
            logger.info(f"Fetching Ollama models for user: {current_user.email}")
            response = requests.get(f"{settings.ollama.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            models = response.json()["models"]
            model_names = [model["name"] for model in models]
            
            return {
                "models": model_names,
                "count": len(model_names),
                "provider": "ollama"
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching Ollama models for user {current_user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama service is not available"
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching models for user {current_user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch models"
            )
    
    # Chat Endpoint (Secured)
    @router.post("/chat")
    async def chat_model(
        chat_request: ChatRequest,
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Chat with configured model (secured version)."""
        try:
            logger.info(f"Chat request from user {current_user.email}, thread {chat_request.thread_id}")
            
            # Check if workflow exists for this user and thread
            workflow_key = f"{current_user.id}:{chat_request.thread_id}"
            if workflow_key not in workflow_store:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Model not configured for this thread. Please configure first."
                )
            
            # Get chat session
            chat_session = db.query(ChatSession).filter(
                ChatSession.user_id == current_user.id,
                ChatSession.thread_id == chat_request.thread_id,
                ChatSession.is_active == True
            ).first()
            
            if not chat_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            # Create user message record
            user_message = ChatMessage(
                session_id=chat_session.id,
                role="user",
                content=chat_request.prompt,
                is_error=False
            )
            db.add(user_message)
            
            # Update session activity
            from datetime import datetime
            chat_session.last_activity = datetime.utcnow()
            chat_session.message_count += 1
            
            db.commit()
            
            # Generate response
            config = {"configurable": {"thread_id": chat_request.thread_id}}
            input_messages = [HumanMessage(chat_request.prompt)]
            
            return StreamingResponse(
                generate_secure_response(
                    workflow_key, 
                    input_messages, 
                    config, 
                    current_user, 
                    chat_session, 
                    db
                ),
                media_type="text/event-stream",
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in chat endpoint for user {current_user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Chat request failed"
            )
    
    async def generate_secure_response(
        workflow_key: str, 
        input_messages, 
        config, 
        user: User, 
        session: ChatSession, 
        db: Session
    ):
        """Generate streaming response with security and logging."""
        workflow_app = workflow_store[workflow_key]
        full_response = ""
        
        try:
            logger.info(f"Generating response for user {user.email}")
            
            for chunk, metadata in workflow_app.stream(
                {"messages": input_messages},
                config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessage):
                    content = chunk.content
                    if content:
                        full_response += content
                        yield content
            
            # Save assistant response to database
            if full_response:
                assistant_message = ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=full_response,
                    is_error=False
                )
                db.add(assistant_message)
                session.message_count += 1
                db.commit()
                
                logger.info(f"Response generated successfully for user {user.email}")
            
        except AuthenticationError as e:
            error_msg = f"[ERROR] Authentication failed: {str(e)}"
            logger.error(f"OpenAI authentication error for user {user.email}: {e}")
            
            # Save error message
            error_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=error_msg,
                is_error=True,
                error_message=str(e)
            )
            db.add(error_message)
            db.commit()
            
            yield error_msg
            
        except Exception as e:
            error_msg = f"[ERROR] Internal server error: {str(e)}"
            logger.error(f"Error generating response for user {user.email}: {e}")
            
            # Save error message
            error_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=error_msg,
                is_error=True,
                error_message=str(e)
            )
            db.add(error_message)
            db.commit()
            
            yield error_msg
    
    def _get_client_ip(request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    return router