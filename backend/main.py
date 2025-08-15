import requests
import logging
import re
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional, Dict, List

from langchain_arcade import ToolManager
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from langgraph.store.base import BaseStore

from pydantic import BaseModel, field_validator, Field, SecretStr
import uvicorn
from pathlib import Path
import os
import bleach
from dotenv import load_dotenv
import uuid
from enum import Enum

load_dotenv()

# ==================== Configuration ====================
class Config:
    """Centralized configuration management"""
    
    # Environment variables
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "10000"))
    MAX_THREAD_ID_LENGTH = int(os.getenv("MAX_THREAD_ID_LENGTH", "100"))
    ARCADE_API_KEY = os.getenv("ARCADE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    USER_EMAIL = os.getenv("EMAIL")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4322")
    
    # Rate limiting - ensure proper format
    RATE_LIMIT_CHAT = "30/minute"  # Fixed format
    RATE_LIMIT_CONFIG = "10/minute"  # Fixed format
    RATE_LIMIT_KEYS = "5/minute"  # Added for other endpoints
    RATE_LIMIT_GENERAL = "20/minute"  # General rate limit
    
    # Model defaults
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "4000"))
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))
    
    # Anti-infinite loop protection
    MAX_TOOL_CALLS_PER_TURN = int(os.getenv("MAX_TOOL_CALLS_PER_TURN", "5"))
    MAX_RECURSION_DEPTH = int(os.getenv("MAX_RECURSION_DEPTH", "25"))
    
    # Available toolkits
    DEFAULT_TOOLKITS = ["Gmail", "Slack", "Calendar", "Drive"]

config = Config()

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

# ==================== Application Setup ====================
app = FastAPI(
    title="Enhanced LocalAI Chat API",
    description="Secure chat interface for LLM models with tool integration",
    version="2.0.0"
)

# ==================== Middleware Setup ====================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

origins = [origin.strip() for origin in config.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

# ==================== Storage Classes ====================
class WorkflowManager:
    """Manages workflow instances and configurations"""
    
    def __init__(self):
        self.workflows: Dict[str, StateGraph] = {}
        self.configurations: Dict[str, Dict] = {}
        self.tool_managers: Dict[str, ToolManager] = {}
    
    def get_workflow(self, thread_id: str) -> Optional[StateGraph]:
        return self.workflows.get(thread_id)
    
    def set_workflow(self, thread_id: str, workflow: StateGraph, config: Dict):
        self.workflows[thread_id] = workflow
        self.configurations[thread_id] = config
    
    def get_config(self, thread_id: str) -> Optional[Dict]:
        return self.configurations.get(thread_id)
    
    def get_tool_manager(self, thread_id: str) -> Optional[ToolManager]:
        return self.tool_managers.get(thread_id)
    
    def set_tool_manager(self, thread_id: str, manager: ToolManager):
        self.tool_managers[thread_id] = manager
    
    def exists(self, thread_id: str) -> bool:
        return thread_id in self.workflows
    
    def delete(self, thread_id: str):
        self.workflows.pop(thread_id, None)
        self.configurations.pop(thread_id, None)
        self.tool_managers.pop(thread_id, None)
    
    def get_current_toolkits(self, thread_id: str) -> List[str]:
        """Get current toolkits from workflow configuration"""
        config = self.configurations.get(thread_id, {})
        return config.get("toolkits", [])
    
    def reconfigure_workflow_tools(self, thread_id: str, new_toolkits: List[str], api_key: Optional[str] = None):
        """Reconfigure existing workflow with new tools while preserving model configuration"""
        if not self.exists(thread_id):
            raise ValueError(f"Thread {thread_id} does not exist")
        
        # Get existing configuration and current toolkits
        current_config = self.configurations[thread_id].copy()
        old_toolkits = current_config.get("toolkits", [])
        
        # Determine changes for system message
        added_tools = set(new_toolkits or []) - set(old_toolkits)
        removed_tools = set(old_toolkits) - set(new_toolkits or [])
        
        # Update toolkits in configuration
        current_config["toolkits"] = new_toolkits or []
        
        # Get current model configuration from existing config
        provider = current_config.get("provider", ModelProvider.OLLAMA)
        model = current_config.get("model", "llama3.2")
        
        # Create model instance with existing configuration
        # We need to get the model parameters from the existing workflow
        # For now, we'll use defaults but this could be enhanced to preserve exact model settings
        model_instance = ModelFactory.create_model(
            provider=provider,
            model_name=model,
            api_key=api_key,  # Use provided API key for tool operations
            temperature=config.DEFAULT_TEMPERATURE,
            max_tokens=config.DEFAULT_MAX_TOKENS
        )
        
        # Initialize tool manager if toolkits specified
        tool_manager = None
        tools = []
        if new_toolkits:
            tool_manager = ToolManager(api_key=config.ARCADE_API_KEY)
            tool_manager.init_tools(toolkits=new_toolkits)
            tools = tool_manager.to_langchain(use_interrupts=True)
            self.set_tool_manager(thread_id, tool_manager)
            
            # Bind tools to model
            model_instance = model_instance.bind_tools(tools)
        else:
            # Remove tool manager if no toolkits
            self.tool_managers.pop(thread_id, None)
        
        # Build new workflow
        workflow = StateGraph(state_schema=MessagesState)
        
        # Add agent node
        agent_node = WorkflowBuilder.create_agent_node(model_instance, tool_manager)
        workflow.add_node("agent", agent_node)
        
        # Add tool nodes if tools are configured
        if tools:
            tool_node = WorkflowBuilder.create_tool_node(tools)
            workflow.add_node("tools", tool_node)
            
            if tool_manager:
                auth_node = WorkflowBuilder.create_authorization_node(tool_manager)
                workflow.add_node("authorization", auth_node)
            
            # Add routing
            routing_func = create_routing_function(
                tool_manager, 
                config.MAX_TOOL_CALLS_PER_TURN
            )
            workflow.add_conditional_edges("agent", routing_func, ["authorization", "tools", END])
            workflow.add_edge("authorization", "tools")
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        workflow.add_edge(START, "agent")
        
        # Update stored workflow and configuration
        self.workflows[thread_id] = workflow
        self.configurations[thread_id] = current_config
        
        # Return workflow and change information
        return {
            "workflow": workflow,
            "changes": {
                "added_tools": list(added_tools),
                "removed_tools": list(removed_tools),
                "old_toolkits": old_toolkits,
                "new_toolkits": new_toolkits or []
            }
        }

workflow_manager = WorkflowManager()

# ==================== Model Providers ====================
class ModelProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class ModelFactory:
    """Factory for creating language models"""
    
    @staticmethod
    def create_model(
        provider: ModelProvider,
        model_name: str,
        api_key: Optional[str] = None,
        temperature: float = config.DEFAULT_TEMPERATURE,
        max_tokens: int = config.DEFAULT_MAX_TOKENS,
        streaming: bool = True
    ):
        """Create a language model based on provider"""
        
        if provider == ModelProvider.OPENAI:
            if not api_key:
                raise ValueError("API key required for OpenAI")
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                timeout=config.DEFAULT_TIMEOUT,
                max_retries=2,
                api_key=SecretStr(api_key),
                streaming=streaming
            )
        
        elif provider == ModelProvider.OLLAMA:
            return ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url=config.OLLAMA_BASE_URL
            )
        
        elif provider == ModelProvider.ANTHROPIC:
            if not api_key:
                raise ValueError("API key required for Anthropic")
            return ChatAnthropic(
                model_name=model_name,
                temperature=temperature,
                api_key=SecretStr(api_key),
                streaming=streaming,
                timeout=config.DEFAULT_TIMEOUT,
                stop=None
            )
        
        elif provider == ModelProvider.GOOGLE:
            if not api_key:
                raise ValueError("API key required for Google")
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=api_key,
                streaming=streaming
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")

# ==================== Validation Utilities ====================
def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize and validate string input"""
    if not isinstance(value, str):
        raise ValueError("Input must be a string")
    
    sanitized = bleach.clean(value, tags=[], attributes={}, strip=True)
    
    if len(sanitized) > max_length:
        raise ValueError(f"Input too long. Maximum {max_length} characters allowed")
    
    return sanitized.strip()

def validate_thread_id(thread_id: str) -> str:
    """Validate thread ID format"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', thread_id):
        raise ValueError("Thread ID can only contain alphanumeric characters, underscores, and hyphens")
    
    if len(thread_id) > config.MAX_THREAD_ID_LENGTH:
        raise ValueError(f"Thread ID too long. Maximum {config.MAX_THREAD_ID_LENGTH} characters allowed")
    
    return thread_id

def create_tool_change_system_message(changes: dict, tool_manager: Optional[ToolManager] = None) -> str:
    """Create a system message explaining tool configuration changes"""
    added_tools = changes.get("added_tools", [])
    removed_tools = changes.get("removed_tools", [])
    new_toolkits = changes.get("new_toolkits", [])
    
    if not added_tools and not removed_tools:
        return ""
    
    message_parts = ["[SYSTEM] Your tool configuration has been updated:"]
    
    if added_tools:
        message_parts.append(f"✅ Added tools: {', '.join(added_tools)}")
    
    if removed_tools:
        message_parts.append(f"❌ Removed tools: {', '.join(removed_tools)}")
    
    if new_toolkits:
        message_parts.append(f"📋 Current available tools: {', '.join(new_toolkits)}")
        
        # Add authorization status for new tools
        if tool_manager and new_toolkits:
            auth_required = []
            for toolkit in new_toolkits:
                if hasattr(tool_manager, 'requires_auth') and tool_manager.requires_auth(toolkit):
                    auth_required.append(toolkit)
            
            if auth_required:
                message_parts.append(f"🔐 Tools requiring authorization: {', '.join(auth_required)}")
    else:
        message_parts.append("📋 No tools are currently available")
    
    message_parts.append("You can now use your updated tool configuration to assist with requests.")
    
    return "\n".join(message_parts)

# ==================== Message Serialization ====================
def serialize_message(message) -> dict:
    """Serialize any type of LangChain message"""
    if hasattr(message, 'type') or isinstance(message, BaseMessage):
        return {
            "type": getattr(message, 'type', 'unknown'),
            "content": getattr(message, 'content', ''),
            "additional_kwargs": getattr(message, 'additional_kwargs', {}),
            "response_metadata": getattr(message, 'response_metadata', {}),
            "id": getattr(message, 'id', None),
            "tool_calls": getattr(message, 'tool_calls', []),
            "usage_metadata": getattr(message, 'usage_metadata', {}),
            "tool_call_id": getattr(message, 'tool_call_id', None),
            "name": getattr(message, 'name', None),
        }
    return message

# ==================== Workflow Components ====================
class WorkflowBuilder:
    """Builder for creating workflow graphs"""
    
    @staticmethod
    def create_agent_node(model, tool_manager: Optional[ToolManager] = None):
        """Create an agent node with streaming support"""
        
        async def call_agent(state: MessagesState, writer, config: RunnableConfig, *, store: BaseStore):
            messages = state["messages"]
            user_id = config.get("configurable", {}).get("user_id", "").replace(".", "")
            namespace = ("memories", user_id)
            
            # Retrieve relevant memories
            memories_str = ""
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, (HumanMessage, dict)) and (
                    isinstance(msg, HumanMessage) or msg.get('type') == 'human'
                ):
                    last_user_message = msg
                    break
            
            if last_user_message and store:
                content = (
                    last_user_message.content 
                    if hasattr(last_user_message, 'content') 
                    else last_user_message.get('content', '')
                )
                try:
                    memories = await store.asearch(namespace, query=str(content))
                    if memories:
                        memories_str = "\n".join([f"- {d.value['data']}" for d in memories])
                except Exception as e:
                    logger.warning(f"Error retrieving memories: {e}")
            
            # Build system message
            system_content = WorkflowBuilder._build_system_message(memories_str, tool_manager)
            messages_with_system = WorkflowBuilder._ensure_system_message(messages, system_content)
            
            # Check for memory storage request
            if last_user_message and store:
                content_str = str(
                    last_user_message.content 
                    if hasattr(last_user_message, 'content') 
                    else last_user_message.get('content', '')
                )
                if "remember" in content_str.lower():
                    try:
                        await store.aput(namespace, str(uuid.uuid4()), {"data": content_str})
                    except Exception as e:
                        logger.warning(f"Error storing memory: {e}")
            
            # Stream response
            full_content = ""
            tool_calls = []
            
            try:
                async for chunk in model.astream(messages_with_system):
                    if chunk.content:
                        writer(chunk.content)
                        full_content += chunk.content
                    
                    if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                        valid_calls = [
                            tc for tc in chunk.tool_calls 
                            if tc.get("name", "").strip()
                        ]
                        tool_calls.extend(valid_calls)
                
                response = AIMessage(content=full_content, tool_calls=tool_calls)
                return {"messages": [serialize_message(response)]}
                
            except Exception as e:
                logger.error(f"Error in agent node: {e}")
                error_msg = AIMessage(content=f"I encountered an error: {str(e)}")
                return {"messages": [serialize_message(error_msg)]}
        
        return call_agent
    
    @staticmethod
    def _build_system_message(memories_str: str, tool_manager: Optional[ToolManager]) -> str:
        """Build system message with memories and tool instructions"""
        base_msg = "You are a helpful AI assistant"
        
        if tool_manager:
            base_msg += " with access to various tools. Always provide required parameters when using tools."
        
        if memories_str:
            base_msg += f"\n\nUser memories:\n{memories_str}"
        
        return base_msg
    
    @staticmethod
    def _ensure_system_message(messages: list, system_content: str) -> list:
        """Ensure system message is present at the beginning"""
        messages_copy = messages[:]
        
        if not messages or not (
            isinstance(messages[0], SystemMessage) or 
            (isinstance(messages[0], dict) and messages[0].get('type') == 'system')
        ):
            system_dict = {"type": "system", "content": system_content}
            messages_copy = [system_dict] + messages_copy
        
        return messages_copy
    
    @staticmethod
    def create_tool_node(tools: list) -> ToolNode:
        """Create a tool node with proper error handling"""
        tool_node = ToolNode(tools)
        
        async def wrapped_tool_node(state: MessagesState):
            try:
                result = await tool_node.ainvoke(state)
                
                if "messages" in result:
                    serialized_messages = [
                        serialize_message(msg) for msg in result["messages"]
                    ]
                    result["messages"] = serialized_messages
                
                return result
                
            except Exception as e:
                logger.error(f"Error in tool node: {e}")
                error_messages = []
                
                last_message = state["messages"][-1]
                tool_calls = (
                    last_message.get("tool_calls", []) 
                    if isinstance(last_message, dict) 
                    else getattr(last_message, 'tool_calls', [])
                )
                
                for tool_call in tool_calls:
                    error_msg = {
                        "type": "tool",
                        "content": f"Error executing tool: {str(e)}",
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_call.get("name", "unknown"),
                    }
                    error_messages.append(error_msg)
                
                return {"messages": error_messages}
        
        return wrapped_tool_node
    
    @staticmethod
    def create_authorization_node(tool_manager: ToolManager):
        """Create an authorization node for tools requiring auth"""
        
        async def authorize(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
            user_id = config["configurable"].get("user_id")
            last_message = state["messages"][-1]
            
            tool_calls = (
                last_message.get("tool_calls", []) 
                if isinstance(last_message, dict) 
                else getattr(last_message, 'tool_calls', [])
            )
            
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                if not tool_manager.requires_auth(tool_name):
                    continue
                
                try:
                    auth_response = tool_manager.authorize(tool_name, user_id)
                    if auth_response.status != "completed":
                        logger.info(f"Authorization required for {tool_name}")
                        logger.info(f"Auth URL: {auth_response.url}")
                        tool_manager.wait_for_auth(auth_response.id)
                        
                        if not tool_manager.is_authorized(auth_response.id):
                            raise ValueError(f"Authorization failed for {tool_name}")
                            
                except Exception as e:
                    logger.error(f"Authorization error for {tool_name}: {e}")
                    raise e
            
            return {"messages": []}
        
        return authorize

# ==================== Routing Logic ====================
def create_routing_function(tool_manager: Optional[ToolManager], max_tool_calls: int = 5):
    """Create a routing function with anti-infinite loop protection"""
    
    def should_continue(state: MessagesState):
        last_message = state["messages"][-1]
        
        # Extract tool calls
        tool_calls = (
            last_message.get("tool_calls", []) 
            if isinstance(last_message, dict) 
            else getattr(last_message, 'tool_calls', [])
        )
        
        # Count recent tool calls for loop protection
        recent_tool_calls = 0
        for msg in state["messages"][-10:]:
            if isinstance(msg, dict):
                recent_tool_calls += len(msg.get("tool_calls", []))
            else:
                recent_tool_calls += len(getattr(msg, 'tool_calls', []))
        
        # Prevent infinite loops
        if recent_tool_calls > max_tool_calls:
            logger.warning("Max tool calls reached, forcing end")
            return END
        
        if not tool_calls:
            return END
        
        # Check for authorization requirements
        if tool_manager:
            for tool_call in tool_calls:
                if tool_manager.requires_auth(tool_call["name"]):
                    return "authorization"
        
        return "tools"
    
    return should_continue

# ==================== API Models ====================
class ConfigRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    provider: ModelProvider
    api_key: Optional[str] = Field(None, max_length=500)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    toolkits: Optional[List[str]] = Field(default_factory=list)
    enable_memory: bool = Field(default=True)
    
    @field_validator('thread_id')
    def validate_thread_id_format(cls, v):
        return validate_thread_id(v)

class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1, max_length=10000)
    
    @field_validator('thread_id')
    def validate_thread_id_format(cls, v):
        return validate_thread_id(v)
    
    @field_validator('prompt')
    def validate_prompt(cls, v):
        return sanitize_string(v, config.MAX_PROMPT_LENGTH)

class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1, max_length=10000)
    
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
        return sanitize_string(v, config.MAX_PROMPT_LENGTH)

# ==================== API Endpoints ====================

@app.post("/chat")
@limiter.limit("30/minute")
async def chat(request: Request, chat_req: ChatRequest):
    """Chat with a model, configuring it automatically on first request"""
    try:
        # Check if thread already exists
        if not workflow_manager.exists(chat_req.thread_id):
            # Auto-configure on first request
            logger.info(f"Auto-configuring model for new thread {chat_req.thread_id}")
            
            # Use provided config or defaults
            provider = chat_req.provider or ModelProvider.OLLAMA
            model = chat_req.model or "llama3.2"  # Default Ollama model
            
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
                temperature=chat_req.temperature or config.DEFAULT_TEMPERATURE,
                max_tokens=chat_req.max_tokens or config.DEFAULT_MAX_TOKENS
            )
            
            # Initialize tool manager if toolkits specified
            tool_manager = None
            tools = []
            if chat_req.toolkits:
                tool_manager = ToolManager(api_key=config.ARCADE_API_KEY)
                tool_manager.init_tools(toolkits=chat_req.toolkits)
                tools = tool_manager.to_langchain(use_interrupts=True)
                workflow_manager.set_tool_manager(chat_req.thread_id, tool_manager)
                
                # Bind tools to model
                model_instance = model_instance.bind_tools(tools)
            
            # Build workflow
            workflow = StateGraph(state_schema=MessagesState)
            
            # Add agent node
            agent_node = WorkflowBuilder.create_agent_node(model_instance, tool_manager)
            workflow.add_node("agent", agent_node)
            
            # Add tool nodes if tools are configured
            if tools:
                tool_node = WorkflowBuilder.create_tool_node(tools)
                workflow.add_node("tools", tool_node)
                
                if tool_manager:
                    auth_node = WorkflowBuilder.create_authorization_node(tool_manager)
                    workflow.add_node("authorization", auth_node)
                
                # Add routing
                routing_func = create_routing_function(
                    tool_manager, 
                    config.MAX_TOOL_CALLS_PER_TURN
                )
                workflow.add_conditional_edges("agent", routing_func, ["authorization", "tools", END])
                workflow.add_edge("authorization", "tools")
                workflow.add_edge("tools", "agent")
            else:
                workflow.add_edge("agent", END)
            
            workflow.add_edge(START, "agent")
            
            # Store workflow
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
            
            logger.info(f"Successfully auto-configured thread {chat_req.thread_id}")
        
        else:
            # Thread already exists - check if tools need to be reconfigured
            current_toolkits = workflow_manager.get_current_toolkits(chat_req.thread_id)
            requested_toolkits = chat_req.toolkits or []
            
            # Compare toolkits (order-independent comparison)
            if set(current_toolkits) != set(requested_toolkits):
                logger.info(f"Reconfiguring tools for thread {chat_req.thread_id}: {current_toolkits} -> {requested_toolkits}")
                
                # Validate API key for tool operations if tools are being added
                if requested_toolkits and not config.ARCADE_API_KEY:
                    raise HTTPException(
                        status_code=400,
                        detail="Arcade API key required for tool operations"
                    )
                
                # Reconfigure workflow with new tools
                try:
                    reconfigure_result = workflow_manager.reconfigure_workflow_tools(
                        chat_req.thread_id, 
                        requested_toolkits,
                        chat_req.api_key
                    )
                    
                    # Create system message about tool changes
                    current_tool_manager = workflow_manager.get_tool_manager(chat_req.thread_id)
                    tool_change_message = create_tool_change_system_message(
                        reconfigure_result["changes"], 
                        current_tool_manager
                    )
                    
                    logger.info(f"Successfully reconfigured tools for thread {chat_req.thread_id}")
                except Exception as e:
                    logger.error(f"Error reconfiguring tools: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error reconfiguring tools: {str(e)}")
            else:
                logger.debug(f"No tool changes needed for thread {chat_req.thread_id}")
                tool_change_message = ""  # No changes, no message
        
        # Proceed with chat
        runtime_config = {
            "configurable": {
                "thread_id": chat_req.thread_id,
                "user_id": config.USER_EMAIL or "default_user"
            },
            "recursion_limit": config.MAX_RECURSION_DEPTH
        }
        
        # Prepare input messages
        input_messages = []
        
        # Add tool change notification as system message if tools were reconfigured
        if 'tool_change_message' in locals() and tool_change_message:
            input_messages.append({
                "type": "system",
                "content": tool_change_message
            })
        
        # Add user message
        input_messages.append({
            "type": "human",
            "content": chat_req.prompt
        })
        
        return StreamingResponse(
            generate_response(chat_req.thread_id, input_messages, runtime_config),
            media_type="text/event-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_response(thread_id: str, input_messages: list, runtime_config: dict):
    """Generate streaming response from workflow"""
    workflow = workflow_manager.get_workflow(thread_id)
    workflow_config = workflow_manager.get_config(thread_id)

    if workflow is None:
        logger.error(f"No workflow found for thread_id: {thread_id}")
        raise HTTPException(status_code=404, detail="Workflow not found for the given thread_id")

    # Check if we should use memory/persistence
    use_memory = (
        workflow_config is not None and
        workflow_config.get("enable_memory", False) and
        config.DATABASE_URL
    )

    if use_memory:
        try:
            # Use async context managers for PostgreSQL components
            async with (AsyncPostgresStore.from_conn_string(config.DATABASE_URL) as store,
                        AsyncPostgresSaver.from_conn_string(config.DATABASE_URL) as checkpointer):
                    logger.info(f"Initialized storage for thread {thread_id}")

                    # Compile workflow with storage
                    workflow_app = workflow.compile(
                        checkpointer=checkpointer,
                        store=store
                    )

                    # Stream response with storage context
                    async for chunk, metadata in workflow_app.astream(
                        {"messages": input_messages},
                        runtime_config,
                        stream_mode="messages"
                    ):
                        if isinstance(chunk, AIMessage):
                            content = str(chunk.content) if chunk.content else ""
                            if content:
                                print(content.encode('utf-8', errors='ignore').decode('utf-8'))
                                yield content.encode('utf-8', errors='ignore').decode('utf-8')
                    return  # Exit after successful completion with storage

        except Exception as e:
            logger.warning(f"Could not initialize storage, continuing without persistence: {e}")
            # Fall through to run without storage

    # Run without storage (either not enabled or initialization failed)
    try:
        # Compile workflow without storage
        workflow_app = workflow.compile()

        # Stream response without storage
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

@app.get("/threads/{thread_id}/status")
async def get_thread_status(thread_id: str):
    """Get the status and configuration of a thread"""
    if not workflow_manager.exists(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    
    config = workflow_manager.get_config(thread_id)
    return {
        "thread_id": thread_id,
        "status": "configured",
        "configuration": config
    }

@app.delete("/threads/{thread_id}")
@limiter.limit("5/minute")
async def delete_thread(request: Request, thread_id: str):
    """Delete a thread and its configuration"""
    if not workflow_manager.exists(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    
    workflow_manager.delete(thread_id)
    return {"status": "success", "message": f"Thread {thread_id} deleted"}

@app.get("/models")
@limiter.limit("20/minute")
async def list_models(request: Request, provider: Optional[ModelProvider] = None):
    """List available models by provider"""
    models = {}
    
    if not provider or provider == ModelProvider.OLLAMA:
        try:
            response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=10)
            response.raise_for_status()
            ollama_models = response.json()["models"]
            models["ollama"] = [model["name"] for model in ollama_models]
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {e}")
            models["ollama"] = []
            return f"Error fetching Ollama models: {e}"
    
    if not provider or provider == ModelProvider.OPENAI:
        models["openai"] = [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    if not provider or provider == ModelProvider.ANTHROPIC:
        models["anthropic"] = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    if not provider or provider == ModelProvider.GOOGLE:
        models["google"] = [
            "gemini-pro",
            "gemini-pro-vision"
        ]
    
    return models

@app.get("/toolkits")
async def list_toolkits():
    """List available tool toolkits"""
    return {
        "available_toolkits": config.DEFAULT_TOOLKITS,
        "description": "These toolkits can be enabled when configuring a thread"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "active_threads": len(workflow_manager.workflows)
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Enhanced LocalAI Chat API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "chat": "POST /chat - Chat with auto-configuration on first request",
            "chat-legacy": "POST /chat-legacy - Chat with pre-configured model (legacy)",
            "models": "GET /models - List available models",
            "toolkits": "GET /toolkits - List available tool toolkits",
            "thread_status": "GET /threads/{thread_id}/status - Get thread status",
            "delete_thread": "DELETE /threads/{thread_id} - Delete a thread",
            "health": "GET /health - Health check"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)