"""
Enhanced LocalAI Chat API - Main Application

A secure chat interface for interacting with various LLM providers
with tool integration capabilities.
"""
import logging
import json
import base64
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from langchain_arcade import ArcadeToolManager
from langchain_core.messages import AIMessage
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.store.sqlite import AsyncSqliteStore
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from dotenv import load_dotenv

load_dotenv()

# PostgreSQL imports - optional for development
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.store.postgres import AsyncPostgresStore
    POSTGRES_AVAILABLE = True
except ImportError:
    AsyncPostgresSaver = None
    AsyncPostgresStore = None
    POSTGRES_AVAILABLE = False

# Initialize settings early for use throughout the app
from config.settings import get_settings
settings = get_settings()

# Import core modules
from core import (
    ModelProvider,
    ModelFactory,
    WorkflowManager,
    WorkflowBuilder,
    ChatRequest,
    validate_thread_id,
    sanitize_string,
    create_routing_function,
    create_tool_change_system_message,
)

# ==================== Logging Setup ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import database components
from database.base import get_db, Base, engine
from database.models import User


# Initialize database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on application startup and cleanup on shutdown."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

    yield


# ==================== Application Setup ====================
app = FastAPI(
    title="Enhanced LocalAI Chat API",
    description="Secure chat interface for LLM models with tool integration",
    version="2.0.0",
    lifespan=lifespan
)

# ==================== Middleware Setup ====================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
from middleware.auth import AuthenticationMiddleware
from middleware.input_sanitization import InputSanitizationMiddleware
from services.security.rate_limiting_middleware import EnhancedRateLimitMiddleware

app.add_middleware(InputSanitizationMiddleware, settings=settings)
app.add_middleware(AuthenticationMiddleware, settings=settings)
app.add_middleware(EnhancedRateLimitMiddleware, settings=settings)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

# Import and add routers
from routers.auth import router as auth_router
from routers.admin import router as admin_router
app.include_router(auth_router)
app.include_router(admin_router)

# Import authentication dependencies
from services.security import get_current_active_user, get_admin_user, get_optional_user
from services.document_service import DocumentProcessor

# Initialize workflow manager
workflow_manager = WorkflowManager()


# ==================== Response Generator ====================
async def generate_response(thread_id: str, input_messages: list, runtime_config: dict):
    """Generate streaming response from workflow."""
    workflow = workflow_manager.get_workflow(thread_id)
    workflow_config = workflow_manager.get_config(thread_id)

    if workflow is None:
        logger.error(f"No workflow found for thread_id: {thread_id}")
        raise HTTPException(status_code=404, detail="Workflow not found for the given thread_id")

    # Check if we should use memory/persistence
    use_memory = (
        workflow_config is not None and
        workflow_config.get("enable_memory", True) and
        settings.database.url
    )

    # Determine database type from URL
    is_sqlite = settings.database.url.startswith("sqlite://")
    is_postgres = settings.database.url.startswith("postgresql://")

    if use_memory:
        try:
            if is_sqlite:
                # Convert SQLite URL format to file path for LangGraph
                sqlite_file_path = settings.database.url.replace("sqlite:///./", "").replace("sqlite:///", "")

                async with (AsyncSqliteStore.from_conn_string(sqlite_file_path) as store,
                            AsyncSqliteSaver.from_conn_string(sqlite_file_path) as checkpointer):
                    logger.info(f"Initialized SQLite storage for thread {thread_id}")

                    workflow_app = workflow.compile(
                        checkpointer=checkpointer,
                        store=store
                    )

                    async for chunk, metadata in workflow_app.astream(
                        {"messages": input_messages},
                        runtime_config,
                        stream_mode="messages"
                    ):
                        if isinstance(chunk, AIMessage):
                            content = str(chunk.content) if chunk.content else ""
                            if content:
                                yield content.encode('utf-8', errors='ignore').decode('utf-8')
                    return

            elif is_postgres and POSTGRES_AVAILABLE:
                async with (AsyncPostgresStore.from_conn_string(settings.database.url) as store,
                            AsyncPostgresSaver.from_conn_string(settings.database.url) as checkpointer):
                    logger.info(f"Initialized PostgreSQL storage for thread {thread_id}")

                    workflow_app = workflow.compile(
                        checkpointer=checkpointer,
                        store=store
                    )

                    async for chunk, metadata in workflow_app.astream(
                        {"messages": input_messages},
                        runtime_config,
                        stream_mode="messages"
                    ):
                        if isinstance(chunk, AIMessage):
                            content = str(chunk.content) if chunk.content else ""
                            if content:
                                yield content.encode('utf-8', errors='ignore').decode('utf-8')
                    return

            else:
                if is_postgres and not POSTGRES_AVAILABLE:
                    logger.warning("PostgreSQL URL provided but PostgreSQL dependencies not available")
                else:
                    logger.warning(f"Unsupported database URL format: {settings.database.url}")
                raise Exception("Unsupported database configuration")

        except Exception as e:
            logger.warning(f"Could not initialize storage, continuing without persistence: {e}")

    # Run without storage (either not enabled or initialization failed)
    try:
        workflow_app = workflow.compile()

        async for chunk, metadata in workflow_app.astream(
            {"messages": input_messages},
            runtime_config,
            stream_mode="messages"
        ):
            if isinstance(chunk, AIMessage):
                content = str(chunk.content) if chunk.content else ""
                if content:
                    yield content.encode('utf-8', errors='ignore').decode('utf-8')

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        yield f"[ERROR] {str(e)}"


# ==================== Helper Functions ====================
def _build_workflow(
    model_instance,
    tool_manager: Optional[ArcadeToolManager],
    tools: list
) -> StateGraph:
    """Build a LangGraph workflow with the given model and tools."""
    workflow = StateGraph(state_schema=MessagesState)

    agent_node = WorkflowBuilder.create_agent_node(model_instance, tool_manager)
    workflow.add_node("agent", agent_node)

    if tools:
        tool_node = WorkflowBuilder.create_tool_node(tools)
        workflow.add_node("tools", tool_node)

        if tool_manager:
            auth_node = WorkflowBuilder.create_authorization_node(tool_manager)
            workflow.add_node("authorization", auth_node)

        routing_func = create_routing_function(
            tool_manager,
            settings.max_tool_calls_per_turn
        )
        workflow.add_conditional_edges("agent", routing_func, ["authorization", "tools", END])
        workflow.add_edge("authorization", "tools")
        workflow.add_edge("tools", "agent")
    else:
        workflow.add_edge("agent", END)

    workflow.add_edge(START, "agent")
    return workflow


def _setup_tools(toolkits: List[str], thread_id: str):
    """Initialize tools and tool manager for the given toolkits."""
    tool_manager = ArcadeToolManager(api_key=settings.arcade_api_key)
    tool_manager.init_tools(toolkits=toolkits)
    tools = tool_manager.to_langchain(use_interrupts=True)

    logger.info(f"Binding {len(tools)} tools to model for thread {thread_id}")
    for i, tool in enumerate(tools):
        tool_name = getattr(tool, 'name', 'Unknown')
        logger.info(f"Tool {i+1}/{len(tools)}: {tool_name}")

    workflow_manager.set_tool_manager(thread_id, tool_manager)
    return tool_manager, tools


def _process_document(filename: str, content: str) -> str:
    """Process an uploaded document and return formatted content."""
    try:
        # Try to decode if it's base64, otherwise treat as text
        if content.startswith('data:'):
            header, data = content.split(',', 1)
            document_bytes = base64.b64decode(data)
        else:
            document_bytes = content.encode('utf-8')
    except Exception:
        document_bytes = content.encode('utf-8')

    processing_result = DocumentProcessor.process_document(filename, document_bytes)

    if processing_result['success']:
        logger.info(f"Successfully processed document: {filename} "
                   f"({len(processing_result['text_content'])} characters)")
        return processing_result['text_content']

    logger.warning(f"Document processing failed: {processing_result['error']}")
    return None


# ==================== API Endpoints ====================
@app.post("/chat")
@limiter.limit("30/minute")
async def chat(
    request: Request,
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Chat with a model, configuring it automatically on first request."""
    try:
        tool_change_message = ""

        # Check if thread already exists
        if not workflow_manager.exists(chat_req.thread_id):
            # Auto-configure on first request
            logger.info(f"Auto-configuring model for new thread {chat_req.thread_id}")

            provider = chat_req.provider or ModelProvider.OLLAMA
            model = chat_req.model or "llama3.2"

            # Validate required parameters for non-Ollama providers
            if provider != ModelProvider.OLLAMA and not chat_req.api_key:
                raise HTTPException(
                    status_code=400,
                    detail=f"API key required for {provider.value} provider"
                )

            # Create model
            model_instance = ModelFactory.create_model(
                provider=provider,
                model_name=model,
                api_key=chat_req.api_key,
                temperature=chat_req.temperature or settings.default_temperature,
                max_tokens=chat_req.max_tokens or settings.default_max_tokens
            )

            # Initialize tools if specified
            tool_manager = None
            tools = []
            if chat_req.toolkits:
                tool_manager, tools = _setup_tools(chat_req.toolkits, chat_req.thread_id)
                model_instance = model_instance.bind_tools(tools)

            # Build and store workflow
            workflow = _build_workflow(model_instance, tool_manager, tools)
            workflow_manager.set_workflow(
                chat_req.thread_id,
                workflow,
                {
                    "provider": provider,
                    "model": model,
                    "toolkits": chat_req.toolkits or [],
                    "enable_memory": chat_req.enable_memory
                }
            )

        else:
            # Thread exists - check if tools need reconfiguration
            current_toolkits = workflow_manager.get_current_toolkits(chat_req.thread_id)
            requested_toolkits = chat_req.toolkits or []

            if set(current_toolkits) != set(requested_toolkits):
                logger.info(f"Reconfiguring tools for thread {chat_req.thread_id}")

                if requested_toolkits and not settings.arcade_api_key:
                    raise HTTPException(
                        status_code=400,
                        detail="Arcade API key required for tool operations"
                    )

                try:
                    reconfigure_result = workflow_manager.reconfigure_workflow_tools(
                        chat_req.thread_id,
                        requested_toolkits,
                        chat_req.api_key
                    )
                    tool_change_message = create_tool_change_system_message(
                        reconfigure_result["changes"]
                    )
                    logger.info(f"Successfully reconfigured tools for thread {chat_req.thread_id}")
                except Exception as e:
                    logger.error(f"Error reconfiguring tools: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error reconfiguring tools: {str(e)}")

        # Prepare runtime config
        runtime_config = {
            "configurable": {
                "thread_id": chat_req.thread_id,
                "user_id": current_user.email or f"user_{current_user.id}"
            },
            "recursion_limit": settings.max_recursion_depth
        }

        # Prepare input messages
        input_messages = []

        if tool_change_message:
            input_messages.append({"type": "system", "content": tool_change_message})

        # Process document if provided
        final_prompt = chat_req.prompt
        if chat_req.document_filename and chat_req.document_content:
            doc_content = _process_document(chat_req.document_filename, chat_req.document_content)
            if doc_content:
                final_prompt = DocumentProcessor.format_document_for_llm(
                    chat_req.prompt,
                    doc_content,
                    chat_req.document_filename
                )
            else:
                final_prompt = f"{chat_req.prompt}\n\n[Note: Could not process uploaded document]"

        input_messages.append({"type": "human", "content": final_prompt})

        # Track usage
        workflow_manager.track_usage(chat_req.thread_id)

        return StreamingResponse(
            generate_response(chat_req.thread_id, input_messages, runtime_config),
            media_type="text/event-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-upload")
@limiter.limit("30/minute")
async def chat_with_upload(
    request: Request,
    thread_id: str = Form(...),
    prompt: str = Form(...),
    model: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    temperature: Optional[float] = Form(None),
    max_tokens: Optional[int] = Form(None),
    toolkits: Optional[str] = Form(None),
    enable_memory: bool = Form(True),
    document: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """Chat with a model, with support for file uploads via multipart form data."""
    try:
        # Parse toolkits from JSON string
        parsed_toolkits = []
        if toolkits:
            try:
                parsed_toolkits = json.loads(toolkits)
            except json.JSONDecodeError:
                parsed_toolkits = []

        # Parse provider enum
        parsed_provider = None
        if provider:
            try:
                parsed_provider = ModelProvider(provider.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

        # Validate inputs
        validated_thread_id = validate_thread_id(thread_id)
        sanitized_prompt = sanitize_string(prompt, settings.max_prompt_length)

        # Process document if provided
        final_prompt = sanitized_prompt
        if document and document.filename:
            try:
                document_bytes = await document.read()
                logger.debug(f"Received file upload: {document.filename}, size: {len(document_bytes)} bytes")

                processing_result = DocumentProcessor.process_document(
                    document.filename,
                    document_bytes
                )

                if processing_result['success']:
                    final_prompt = DocumentProcessor.format_document_for_llm(
                        sanitized_prompt,
                        processing_result['text_content'],
                        document.filename
                    )
                    logger.info(f"Successfully processed document: {document.filename}")
                else:
                    final_prompt = f"{sanitized_prompt}\n\n[Note: Could not process uploaded document: {processing_result['error']}]"

            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                final_prompt = f"{sanitized_prompt}\n\n[Note: Error processing uploaded document: {str(e)}]"

        # Setup workflow if new thread
        if not workflow_manager.exists(validated_thread_id):
            logger.info(f"Auto-configuring model for new thread {validated_thread_id}")

            use_provider = parsed_provider or ModelProvider.OLLAMA
            use_model = model or "llama3.2"

            if use_provider != ModelProvider.OLLAMA and not api_key:
                raise HTTPException(
                    status_code=400,
                    detail=f"API key required for {use_provider.value} provider"
                )

            model_instance = ModelFactory.create_model(
                provider=use_provider,
                model_name=use_model,
                api_key=api_key,
                temperature=temperature or settings.default_temperature,
                max_tokens=max_tokens or settings.default_max_tokens
            )

            tool_manager = None
            tools = []
            if parsed_toolkits:
                tool_manager, tools = _setup_tools(parsed_toolkits, validated_thread_id)
                model_instance = model_instance.bind_tools(tools)

            workflow = _build_workflow(model_instance, tool_manager, tools)
            workflow_manager.set_workflow(
                validated_thread_id,
                workflow,
                {
                    "provider": use_provider,
                    "model": use_model,
                    "toolkits": parsed_toolkits,
                    "enable_memory": enable_memory
                }
            )

        # Prepare runtime config
        runtime_config = {
            "configurable": {
                "thread_id": validated_thread_id,
                "user_id": f"user_{current_user.id}" if current_user else validated_thread_id
            },
            "recursion_limit": settings.max_recursion_depth
        }

        input_messages = [{"type": "human", "content": final_prompt}]

        workflow_manager.track_usage(validated_thread_id)

        return StreamingResponse(
            generate_response(validated_thread_id, input_messages, runtime_config),
            media_type="text/event-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat-upload endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/status")
async def get_thread_status(
    thread_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get the status and configuration of a thread."""
    if not workflow_manager.exists(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")

    config = workflow_manager.get_config(thread_id)
    usage_stats = workflow_manager.get_usage_stats(thread_id)

    return {
        "thread_id": thread_id,
        "status": "configured",
        "configuration": config,
        "usage_stats": usage_stats
    }


@app.delete("/threads/{thread_id}")
@limiter.limit("5/minute")
async def delete_thread(
    request: Request,
    thread_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a thread and its configuration."""
    if not workflow_manager.exists(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")

    workflow_manager.delete(thread_id)
    return {"status": "success", "message": f"Thread {thread_id} deleted"}


@app.get("/models")
@limiter.limit("20/minute")
async def list_models(
    request: Request,
    provider: Optional[ModelProvider] = None,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """List available models by provider (returns model IDs only for backward compatibility)."""
    models = {}

    if not provider or provider == ModelProvider.OLLAMA:
        try:
            response = requests.get(f"{settings.ollama.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            ollama_models = response.json()["models"]
            models["ollama"] = [model["name"] for model in ollama_models]
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {e}")
            models["ollama"] = []

    if not provider or provider == ModelProvider.OPENAI:
        models["openai"] = settings.openai_models_list

    if not provider or provider == ModelProvider.ANTHROPIC:
        models["anthropic"] = settings.anthropic_models_list

    if not provider or provider == ModelProvider.GOOGLE:
        models["google"] = settings.google_models_list

    return models


@app.get("/providers")
@limiter.limit("20/minute")
async def list_providers(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all providers with their models (includes display titles).
    This endpoint is designed for frontend consumption.
    """
    config = settings.models_config
    providers_config = config.get("providers", {})

    # Build response with Ollama models fetched dynamically
    result = {}

    for provider_key, provider_data in providers_config.items():
        provider_info = {
            "name": provider_data.get("name", provider_key.title()),
            "requires_api_key": provider_data.get("requires_api_key", True),
            "models": []
        }

        if provider_key == "ollama":
            # Fetch Ollama models dynamically
            try:
                response = requests.get(f"{settings.ollama.base_url}/api/tags", timeout=10)
                response.raise_for_status()
                ollama_models = response.json()["models"]
                provider_info["models"] = [
                    {
                        "title": model["name"],
                        "model": model["name"],
                        "provider": "ollama"
                    }
                    for model in ollama_models
                ]
            except Exception as e:
                logger.error(f"Error fetching Ollama models: {e}")
                provider_info["models"] = []
                provider_info["error"] = "Could not fetch Ollama models"
        else:
            # Use configured models with provider field added
            provider_info["models"] = [
                {
                    "title": m.get("title", m["model"]),
                    "model": m["model"],
                    "provider": provider_key
                }
                for m in provider_data.get("models", [])
            ]

        result[provider_key] = provider_info

    return result


@app.get("/toolkits")
async def list_toolkits(current_user: Optional[User] = Depends(get_optional_user)):
    """List available tool toolkits with capabilities."""
    toolkits = []
    for toolkit in settings.default_toolkits_list:
        toolkits.append({
            "name": toolkit,
            "capability": settings.tool_capabilities.get(toolkit, "General purpose tool")
        })

    return {
        "available_toolkits": toolkits,
        "description": "These toolkits can be enabled when configuring a thread"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "active_threads": len(workflow_manager.workflows)
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Enhanced LocalAI Chat API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "chat": "POST /chat - Chat with auto-configuration on first request",
            "chat-upload": "POST /chat-upload - Chat with file upload support",
            "models": "GET /models - List available model IDs by provider",
            "providers": "GET /providers - List providers with full model details (for frontend)",
            "toolkits": "GET /toolkits - List available tool toolkits",
            "thread_status": "GET /threads/{thread_id}/status - Get thread status",
            "delete_thread": "DELETE /threads/{thread_id} - Delete a thread",
            "health": "GET /health - Health check"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
