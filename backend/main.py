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

from langchain_arcade import ArcadeToolManager
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.sqlite import AsyncSqliteStore
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# PostgreSQL imports - optional for development
try:

    
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.store.postgres import AsyncPostgresStore
    POSTGRES_AVAILABLE = True
except ImportError:
    AsyncPostgresSaver = None
    AsyncPostgresStore = None
    POSTGRES_AVAILABLE = False


from langgraph.store.base import BaseStore

from pydantic import BaseModel, field_validator, Field, SecretStr
import uvicorn
import bleach
from dotenv import load_dotenv
import uuid
import time
from enum import Enum
from prompts import prompt_loader

load_dotenv()

# Initialize settings early for use throughout the app
from config.settings import get_settings
settings = get_settings()

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

# Add input sanitization middleware (should be first for security)
app.add_middleware(InputSanitizationMiddleware, settings=settings)

app.add_middleware(AuthenticationMiddleware, settings=settings)

# Add enhanced rate limiting middleware
enhanced_rate_limiter = EnhancedRateLimitMiddleware(app, settings)
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
from database.models import User
from database.base import get_db, Base, engine
from sqlalchemy.orm import Session
from fastapi import Depends

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        # Don't fail startup - just log the error

# ==================== Storage Classes ====================
class WorkflowManager:
    """Manages workflow instances and configurations"""
    
    def __init__(self):
        self.workflows: Dict[str, StateGraph] = {}
        self.configurations: Dict[str, Dict] = {}
        self.tool_managers: Dict[str, ArcadeToolManager] = {}
        self.usage_stats: Dict[str, Dict] = {}  # Simple usage tracking
    
    def get_workflow(self, thread_id: str) -> Optional[StateGraph]:
        
        return self.workflows.get(thread_id)
    
    def set_workflow(self, thread_id: str, workflow: StateGraph, config: Dict):
        self.workflows[thread_id] = workflow
        self.configurations[thread_id] = config
    
    def get_config(self, thread_id: str) -> Optional[Dict]:
        return self.configurations.get(thread_id)
    
    def get_tool_manager(self, thread_id: str) -> Optional[ArcadeToolManager]:
        return self.tool_managers.get(thread_id)
    
    def set_tool_manager(self, thread_id: str, manager: ArcadeToolManager):
        self.tool_managers[thread_id] = manager
    
    def exists(self, thread_id: str) -> bool:
        return thread_id in self.workflows
    
    def delete(self, thread_id: str):
        self.workflows.pop(thread_id, None)
        self.configurations.pop(thread_id, None)
        self.tool_managers.pop(thread_id, None)
        self.usage_stats.pop(thread_id, None)
    
    def track_usage(self, thread_id: str, tool_name: Optional[str] = None, execution_time: Optional[float] = None):
        """Track simple usage statistics and performance"""
        if thread_id not in self.usage_stats:
            self.usage_stats[thread_id] = {
                "chat_count": 0,
                "tool_usage": {},
                "tool_performance": {},  # Track execution times
                "last_used": datetime.now().isoformat()
            }
        
        self.usage_stats[thread_id]["chat_count"] += 1
        self.usage_stats[thread_id]["last_used"] = datetime.now().isoformat()
        
        if tool_name:
            # Usage count
            if tool_name not in self.usage_stats[thread_id]["tool_usage"]:
                self.usage_stats[thread_id]["tool_usage"][tool_name] = 0
            self.usage_stats[thread_id]["tool_usage"][tool_name] += 1
            
            # Performance tracking
            if execution_time is not None:
                if tool_name not in self.usage_stats[thread_id]["tool_performance"]:
                    self.usage_stats[thread_id]["tool_performance"][tool_name] = {
                        "total_time": 0.0,
                        "call_count": 0,
                        "avg_time": 0.0
                    }
                
                perf = self.usage_stats[thread_id]["tool_performance"][tool_name]
                perf["total_time"] += execution_time
                perf["call_count"] += 1
                perf["avg_time"] = perf["total_time"] / perf["call_count"]
    
    def get_usage_stats(self, thread_id: str) -> Dict:
        """Get usage statistics for a thread"""
        return self.usage_stats.get(thread_id, {})
    

    

    

    
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
            temperature=settings.default_temperature,
            max_tokens=settings.default_max_tokens
        )
        
        # Initialize tool manager if toolkits specified
        tool_manager = None
        tools = []
        if new_toolkits:
            tool_manager = ArcadeToolManager(api_key=settings.arcade_api_key)
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
                settings.max_tool_calls_per_turn
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
        temperature: float = settings.default_temperature,
        max_tokens: int = settings.default_max_tokens,
        streaming: bool = True
    ):
        """Create a language model based on provider"""
        
        if provider == ModelProvider.OPENAI:
            if not api_key:
                raise ValueError("API key required for OpenAI")
            return ChatOpenAI(
                model=model_name,
                # temperature=temperature,
                timeout=settings.default_timeout,
                max_retries=2,
                api_key=SecretStr(api_key),
                streaming=streaming
            )
        
        elif provider == ModelProvider.OLLAMA:
            return ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url=settings.ollama.base_url
            )
        
        elif provider == ModelProvider.ANTHROPIC:
            if not api_key:
                raise ValueError("API key required for Anthropic")
            return ChatAnthropic(
                model_name=model_name,
                temperature=temperature,
                api_key=SecretStr(api_key),
                streaming=streaming,
                timeout=settings.default_timeout,
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
    
    if len(thread_id) > settings.max_thread_id_length:
        raise ValueError(f"Thread ID too long. Maximum {settings.max_thread_id_length} characters allowed")
    
    return thread_id

def create_tool_change_system_message(changes: dict, tool_manager: Optional[ArcadeToolManager] = None) -> str:
    """Create a system message explaining tool configuration changes"""
    added_tools = changes.get("added_tools", [])
    removed_tools = changes.get("removed_tools", [])
    new_toolkits = changes.get("new_toolkits", [])
    if not added_tools and not removed_tools:
        return ""
    
    message_parts = ["[SYSTEM] Your tool configuration has been updated:"]
    
    if added_tools:
        message_parts.append(f"✅ Added tools: {', '.join(added_tools)}")
        # Add capabilities for new tools
        for tool in added_tools:
            capability = settings.tool_capabilities.get(tool, "🔧 General purpose tool")
            message_parts.append(f"   {tool}: {capability}")
    
    if removed_tools:
        message_parts.append(f"❌ Removed tools: {', '.join(removed_tools)}")
    
    if new_toolkits:
        message_parts.append(f"📋 Current available tools: {', '.join(new_toolkits)}")
        
        # Add authorization status for new tools (skip for now to avoid manager issues)
        # Note: Authorization checking disabled due to tool manager initialization issues
        if tool_manager and new_toolkits:
            auth_required = []
            for toolkit in new_toolkits:
                try:
                    if hasattr(tool_manager, 'requires_auth') and tool_manager.requires_auth(toolkit):
                        auth_required.append(toolkit)
                except Exception as e:
                    logger.debug(f"Could not check auth requirements for {toolkit}: {e}")
            
            if auth_required:
                message_parts.append(f"🔐 Tools requiring authorization: {', '.join(auth_required)}")
        
        # Check for tool conflicts
        conflicts = detect_tool_conflicts(new_toolkits)
        if conflicts:
            message_parts.append("⚠️ Potential tool conflicts detected:")
            for conflict in conflicts:
                message_parts.append(f"   {conflict}")
    else:
        message_parts.append("📋 No tools are currently available")
    
    message_parts.append("You can now use your updated tool configuration to assist with requests.")
    return "\n".join(message_parts)

def detect_tool_conflicts(toolkits: List[str]) -> List[str]:
    """Detect potential conflicts between tools"""
    conflicts = []
    
    for tool in toolkits:
        tool_config = settings.tool_conflicts.get(tool, {})
        conflicts_with = tool_config.get("conflicts_with", [])
        
        for other_tool in toolkits:
            if other_tool != tool and other_tool in conflicts_with:
                note = tool_config.get("note", "")
                conflict_msg = f"{tool} may conflict with {other_tool}"
                if note:
                    conflict_msg += f" ({note})"
                conflicts.append(conflict_msg)
    
    return list(set(conflicts))  # Remove duplicates

# ==================== Message Serialization ====================
def serialize_message(message) -> dict:
    """Serialize any type of LangChain message with enhanced status and metadata handling"""
    if hasattr(message, 'type') or isinstance(message, BaseMessage):
        serialized = {
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
        
        # Capture artifact field for tool messages
        if hasattr(message, 'artifact'):
            serialized["artifact"] = getattr(message, 'artifact', None)
            
        # Extract status information from various possible locations
        if serialized["type"] == "tool":
            # Priority order for status determination:
            # 1. Explicit non-default status attribute on message
            # 2. Status in additional_kwargs
            # 3. Success flag in additional_kwargs  
            # 4. Status in response_metadata
            # 5. Error in response_metadata
            # 6. Content pattern analysis
            # 7. Default to success
            
            status_found = False
            
            # Enhanced status handling for ToolMessages - check explicit status first
            # BUT only if it's not the default 'success' value, because tools might
            # have meaningful error information in other fields that overrides the default
            if hasattr(message, 'status'):
                explicit_status = getattr(message, 'status', 'success')
                if explicit_status != 'success':
                    # Only trust non-default status values
                    serialized["status"] = explicit_status
                    status_found = True
                # If status is 'success' (default), continue checking other fields for error indicators
            
            # Check for status in additional_kwargs
            if not status_found:
                additional_kwargs = serialized.get("additional_kwargs", {})
                if "status" in additional_kwargs:
                    serialized["status"] = additional_kwargs["status"]
                    status_found = True
                elif "success" in additional_kwargs:
                    serialized["status"] = "success" if additional_kwargs["success"] else "error"
                    status_found = True
            
            # Check response_metadata for status indicators
            if not status_found:
                response_metadata = serialized.get("response_metadata", {})
                if "status" in response_metadata:
                    serialized["status"] = response_metadata["status"]
                    status_found = True
                elif "error" in response_metadata:
                    serialized["status"] = "error"
                    serialized["error_details"] = response_metadata["error"]
                    status_found = True
            
            # Analyze content for error patterns if no explicit status found
            if not status_found and serialized["content"]:
                content_str = str(serialized["content"]).lower()
                if any(error_pattern in content_str for error_pattern in 
                       ["error:", "failed", "exception", "could not", "unable to"]):
                    serialized["status"] = "error"
                    status_found = True
            
            # Default to success if no status indicators found
            if not status_found:
                serialized["status"] = "success"
        
        return serialized
    return message

# ==================== Workflow Components ====================
class WorkflowBuilder:
    """Builder for creating workflow graphs"""
    
    @staticmethod
    def create_agent_node(model, tool_manager: Optional[ArcadeToolManager] = None):
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
            logger.info(f"System message length: {len(system_content)}")
            logger.debug(f"System message content: {system_content[:500]}...")
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
    def _extract_tool_schemas(tool_manager: ArcadeToolManager) -> str:
        """Extract tool schemas and parameter requirements from tool manager"""
        try:
            # Get the tools from the manager
            tools = tool_manager.to_langchain(use_interrupts=True)
            logger.info(f"Found {len(tools)} tools from tool manager")
            
            if not tools:
                logger.warning("No tools found from tool manager")
                return ""
            
            tool_schemas = []
            for i, tool in enumerate(tools):
                tool_name = getattr(tool, 'name', 'Unknown')
                tool_description = getattr(tool, 'description', 'No description available')
                logger.info(f"Processing tool {i+1}/{len(tools)}: {tool_name}")
                
                # Try to get tool arguments schema
                args_schema = getattr(tool, 'args_schema', None)
                if args_schema:
                    try:
                        # Extract field information from pydantic schema
                        schema_info = args_schema.model_json_schema()
                        properties = schema_info.get('properties', {})
                        required = schema_info.get('required', [])
                        logger.info(f"Tool {tool_name} has {len(properties)} parameters, {len(required)} required")
                        
                        tool_info = f"\n{tool_name}:"
                        tool_info += f"\n- Description: {tool_description}"
                        
                        if properties:
                            tool_info += "\n- Parameters:"
                            for field_name, field_info in properties.items():
                                param_type = field_info.get('type', 'unknown')
                                param_desc = field_info.get('description', 'No description')
                                is_required = field_name in required
                                status = "(REQUIRED)" if is_required else "(optional)"
                                tool_info += f"\n  • {field_name} {status}: {param_desc} (type: {param_type})"
                        
                        tool_schemas.append(tool_info)
                    except Exception as e:
                        logger.warning(f"Failed to extract schema for {tool_name}: {e}")
                        # Fallback for tools without proper schema
                        tool_schemas.append(f"\n{tool_name}:\n- Description: {tool_description}\n- Parameters: Could not extract schema")
                else:
                    logger.warning(f"Tool {tool_name} has no args_schema")
                    tool_schemas.append(f"\n{tool_name}:\n- Description: {tool_description}\n- Parameters: No schema available")
                        
            result = "\n".join(tool_schemas) if tool_schemas else ""
            logger.info(f"Generated schema string length: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Could not extract tool schemas: {e}", exc_info=True)
            return ""
    
    @staticmethod
    def _build_system_message(memories_str: str, tool_manager: Optional[ArcadeToolManager]) -> str:
        """Build system message with memories and detailed tool instructions"""
        return prompt_loader.build_system_message(
            memories_str=memories_str, 
            tool_manager=tool_manager, 
            extract_schemas_func=WorkflowBuilder._extract_tool_schemas
        )
    
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
            # Track tool execution time
            start_time = time.time()
            tool_names = []
            
            # Extract tool names from the last message
            try:
                last_message = state["messages"][-1]
                tool_calls = (
                    last_message.get("tool_calls", []) 
                    if isinstance(last_message, dict) 
                    else getattr(last_message, 'tool_calls', [])
                )
                tool_names = [tc.get("name", "unknown") for tc in tool_calls]
            except:
                pass
            
            try:
                # Log tool execution details
                logger.info(f"Executing tools: {', '.join(tool_names) if tool_names else 'unknown'}")
                logger.debug(f"Tool execution state: {state}")
                
                result = await tool_node.ainvoke(state)
                
                # Enhanced logging of tool results with status information
                execution_time = time.time() - start_time
                logger.info(f"Tool execution completed in {execution_time:.2f}s")
                
                # Process and log tool responses with status information
                if "messages" in result:
                    serialized_messages = []
                    for i, msg in enumerate(result["messages"]):
                        serialized_msg = serialize_message(msg)
                        serialized_messages.append(serialized_msg)
                        
                        # Log detailed tool response information
                        tool_name = serialized_msg.get("name", "unknown")
                        status = serialized_msg.get("status", "unknown")
                        content_preview = str(serialized_msg.get("content", ""))[:100]
                        
                        logger.info(f"Tool '{tool_name}' response {i+1}: status={status}, content_preview='{content_preview}'")
                        
                        # Log additional diagnostic information for tool responses
                        if serialized_msg.get("type") == "tool":
                            if "error_details" in serialized_msg:
                                logger.warning(f"Tool '{tool_name}' error details: {serialized_msg['error_details']}")
                            
                            # Log artifacts if present
                            if serialized_msg.get("artifact"):
                                logger.debug(f"Tool '{tool_name}' has artifact data")
                            
                            # Log additional metadata
                            additional_kwargs = serialized_msg.get("additional_kwargs", {})
                            response_metadata = serialized_msg.get("response_metadata", {})
                            if additional_kwargs:
                                logger.debug(f"Tool '{tool_name}' additional_kwargs: {additional_kwargs}")
                            if response_metadata:
                                logger.debug(f"Tool '{tool_name}' response_metadata: {response_metadata}")
                    
                    result["messages"] = serialized_messages
                    logger.info(f"Processed {len(serialized_messages)} tool response messages")
                else:
                    logger.warning("Tool execution result contains no 'messages' field")
                    logger.debug(f"Raw tool result: {result}")
                
                return result
                
            except Exception as e:
                # Track failed execution time
                execution_time = time.time() - start_time
                logger.error(f"Error in tool node after {execution_time:.2f}s: {e}")
                
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
    def create_authorization_node(tool_manager: ArcadeToolManager):
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
def create_routing_function(tool_manager: Optional[ArcadeToolManager], max_tool_calls: int = 5):
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

class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1, max_length=10000)
    # Document upload fields
    document_filename: Optional[str] = Field(None, max_length=255)
    document_content: Optional[str] = Field(None, max_length=100000)  # Base64 encoded or text content
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

# ==================== API Endpoints ====================

@app.post("/chat")
@limiter.limit("30/minute")
async def chat(
    request: Request, 
    chat_req: ChatRequest, 
    current_user: User = Depends(get_current_active_user)
):
    """Chat with a model, configuring it automatically on first request"""
    try:

        # Check if thread already exists
        if not workflow_manager.exists(chat_req.thread_id):
            # Auto-configure on first request
            logger.info(f"Auto-configuring model for new thread {chat_req.thread_id}")
            
            # Use provided config or defaults
            provider = chat_req.provider or ModelProvider.OLLAMA
            model = chat_req.model or "llama3.2"  # Default Ollama model
            
            # Use user preferences for toolkits if not specified
            
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
            
            # Initialize tool manager if toolkits specified
            tool_manager = None
            tools = []
            if chat_req.toolkits:
                tool_manager = ArcadeToolManager(api_key=settings.arcade_api_key)
                tool_manager.init_tools(toolkits=chat_req.toolkits)
                tools = tool_manager.to_langchain(use_interrupts=True)
                
                # Debug tool binding - focus on Gmail tools
                logger.info(f"Binding {len(tools)} tools to model for thread {chat_req.thread_id}")
                gmail_tools = []
                for i, tool in enumerate(tools):
                    tool_name = getattr(tool, 'name', 'Unknown')
                    tool_desc = getattr(tool, 'description', 'No description')
                    logger.info(f"Tool {i+1}/{len(tools)}: {tool_name} - {tool_desc[:100]}")
                    if 'gmail' in tool_name.lower() or 'email' in tool_name.lower():
                        gmail_tools.append(tool_name)
                
                logger.info(f"Gmail-related tools found: {gmail_tools}")
                if not any('send' in name.lower() for name in gmail_tools):
                    logger.warning("No Gmail Send tool found in available tools!")
                
                workflow_manager.set_tool_manager(chat_req.thread_id, tool_manager)
                
                # Bind tools to model
                model_instance = model_instance.bind_tools(tools)
                logger.info(f"Successfully bound {len(tools)} tools to model")
            
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
                    settings.max_tool_calls_per_turn
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
            

        
        else:
            # Thread already exists - check if tools need to be reconfigured       

            current_toolkits = workflow_manager.get_current_toolkits(chat_req.thread_id)
            requested_toolkits = chat_req.toolkits or []
            # Compare toolkits (order-independent comparison)
            if set(current_toolkits) != set(requested_toolkits):
                logger.info(f"Reconfiguring tools for thread {chat_req.thread_id}: {current_toolkits} -> {requested_toolkits}")
                
                # Validate API key for tool operations if tools are being added
                if requested_toolkits and not settings.arcade_api_key:
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
                    tool_change_message = create_tool_change_system_message(
                        reconfigure_result["changes"]
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
                "user_id": current_user.email or f"user_{current_user.id}"
            },
            "recursion_limit": settings.max_recursion_depth
        }
        
        # Prepare input messages
        input_messages = []
        
        # Add tool change notification as system message if tools were reconfigured
        if 'tool_change_message' in locals() and tool_change_message:
            input_messages.append({
                "type": "system",
                "content": tool_change_message
            })
        
        # Debug logging
        logger.info(f"🔍 Chat request received - document_filename: {chat_req.document_filename}, "
                   f"document_content length: {len(chat_req.document_content) if chat_req.document_content else 0}")
        
        # Process document if provided
        final_prompt = chat_req.prompt
        if chat_req.document_filename and chat_req.document_content:
            try:
                # The frontend sends the document content as text, not base64
                # We need to process it through our document service for validation and formatting
                import base64
                
                # Try to decode if it's base64, otherwise treat as text
                try:
                    if chat_req.document_content.startswith('data:'):
                        # Handle data URLs (data:text/plain;base64,...)
                        header, data = chat_req.document_content.split(',', 1)
                        document_bytes = base64.b64decode(data)
                    else:
                        # Assume it's plain text content from frontend
                        document_bytes = chat_req.document_content.encode('utf-8')
                except Exception:
                    # If decoding fails, treat as text
                    document_bytes = chat_req.document_content.encode('utf-8')
                
                # Process document through our service
                processing_result = DocumentProcessor.process_document(
                    chat_req.document_filename, 
                    document_bytes
                )
                
                if processing_result['success']:
                    # Format the message with document content
                    final_prompt = DocumentProcessor.format_document_for_llm(
                        chat_req.prompt,
                        processing_result['text_content'],
                        chat_req.document_filename
                    )
                    logger.info(f"Successfully processed document: {chat_req.document_filename} "
                              f"({len(processing_result['text_content'])} characters)")
                else:
                    logger.warning(f"Document processing failed: {processing_result['error']}")
                    # Continue with original prompt, but add error message
                    final_prompt = f"{chat_req.prompt}\n\n[Note: Could not process uploaded document '{chat_req.document_filename}': {processing_result['error']}]"
                    
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                # Continue with original prompt but add error note
                final_prompt = f"{chat_req.prompt}\n\n[Note: Error processing uploaded document: {str(e)}]"
        
        # Add user message with processed content
        input_messages.append({
            "type": "human",
            "content": final_prompt
        })
        
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
                # From: sqlite:///./data/dev.db -> data/dev.db
                sqlite_file_path = settings.database.url.replace("sqlite:///./", "").replace("sqlite:///", "")
                
                # Use SQLite components with converted path
                async with (AsyncSqliteStore.from_conn_string(sqlite_file_path) as store,
                            AsyncSqliteSaver.from_conn_string(sqlite_file_path) as checkpointer):
                    logger.info(f"Initialized SQLite storage for thread {thread_id}")
                    
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
                                yield content.encode('utf-8', errors='ignore').decode('utf-8')
                    return  # Exit after successful completion with storage
                    
            elif is_postgres and POSTGRES_AVAILABLE:
                # Use PostgreSQL components
                async with (AsyncPostgresStore.from_conn_string(settings.database.url) as store,
                            AsyncPostgresSaver.from_conn_string(settings.database.url) as checkpointer):
                    logger.info(f"Initialized PostgreSQL storage for thread {thread_id}")
                    
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
                                yield content.encode('utf-8', errors='ignore').decode('utf-8')
                    return  # Exit after successful completion with storage
                    
            else:
                # Unsupported database type or PostgreSQL not available
                if is_postgres and not POSTGRES_AVAILABLE:
                    logger.warning("PostgreSQL URL provided but PostgreSQL dependencies not available")
                else:
                    logger.warning(f"Unsupported database URL format: {settings.database.url}")
                raise Exception("Unsupported database configuration")

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
async def get_thread_status(
    thread_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get the status and configuration of a thread"""
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
    """Delete a thread and its configuration"""
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
    """List available models by provider"""
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
async def list_toolkits(current_user: Optional[User] = Depends(get_optional_user)):
    """List available tool toolkits with capabilities"""
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