import json
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

from langchain_arcade import ToolManager
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from langgraph.store.base import BaseStore

from pydantic import BaseModel, field_validator, Field
from typing import Any, Optional
import openai
from pathlib import Path
import os
import bleach
from dotenv import load_dotenv
from asyncpg import create_pool
import uuid

load_dotenv()

agent_toolkits = ["Gmail"]

app = FastAPI(
    title="LocalAI Chat API",
    description="Secure chat interface for LLM models",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment validation
required_env_vars = []

for var in required_env_vars:
    if not os.getenv(var):
        logger.error(f"Required environment variable {var} is not set")
        raise ValueError(f"Missing required environment variable: {var}")

ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
max_prompt_length = int(os.getenv("MAX_PROMPT_LENGTH", "10000"))
max_thread_id_length = int(os.getenv("MAX_THREAD_ID_LENGTH", "100"))
arcade_api_key = os.getenv("ARCADE_API_KEY")
database_url = os.getenv("DATABASE_URL")
email = os.getenv("EMAIL")

workflow_store: dict[str, Any] = {}
memory_store: dict[str, MemorySaver] = {}

manager = ToolManager(api_key=arcade_api_key)
manager.init_tools(toolkits=agent_toolkits)
tools = manager.to_langchain(use_interrupts=True)

# DEBUG: Print available tools and their schemas
print("🔧 Available tools:")
for i, tool in enumerate(tools):
    print(f"   {i}: {tool.name}")
    print(f"      Description: {getattr(tool, 'description', 'No description')}")
    if hasattr(tool, 'args_schema') and tool.args_schema:
        print(f"      Schema: {tool.args_schema.schema()}")
    else:
        print(f"      Schema: No schema available")
    print(f"      Tool object: {type(tool)}")
    print()

tool_node = ToolNode(tools)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# CORS origins validation
origins_str = os.getenv("CORS_ORIGINS", "http://localhost:4322")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = Path("config/keys.json")

def load_keys():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_keys(data):
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize and validate string input"""
    if not isinstance(value, str):
        raise ValueError("Input must be a string")
    
    # Remove potentially dangerous characters
    sanitized = bleach.clean(value, tags=[], attributes={}, strip=True)
    
    # Limit length
    if len(sanitized) > max_length:
        raise ValueError(f"Input too long. Maximum {max_length} characters allowed")
    
    return sanitized.strip()

def validate_thread_id(thread_id: str) -> str:
    """Validate thread ID format"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', thread_id):
        raise ValueError("Thread ID can only contain alphanumeric characters, underscores, and hyphens")    
    if len(thread_id) > max_thread_id_length:
        raise ValueError(f"Thread ID too long. Maximum {max_thread_id_length} characters allowed")
    return thread_id

def should_continue(state: MessagesState):
    """Fixed version that handles both dict and object formats"""
    last_message = state["messages"][-1]
    
    # Handle both dict and object formats
    if isinstance(last_message, dict):
        tool_calls = last_message.get("tool_calls", [])
        message_type = last_message.get("type", "unknown")
    else:
        tool_calls = getattr(last_message, 'tool_calls', [])
        message_type = getattr(last_message, 'type', "unknown")
    
    print(f"🔧 should_continue - Message type: {message_type}")
    print(f"🔧 should_continue - Tool calls: {len(tool_calls)}")
    
    # CRITICAL: Check for empty args pattern that causes infinite loops
    if tool_calls:
        for tool_call in tool_calls:
            args = tool_call.get("args", {})
            name = tool_call.get("name", "")
            
            # If tool requires parameters but args are empty, create fake response and force END
            # if name in ["Gmail_GetThread", "Gmail_GetEmail", "Gmail_SendEmail"] and not args:
            #     print(f"🔧 CRITICAL: Tool {name} called with empty args - Creating fake response and ending")
                
            #     # Create a fake tool response to satisfy OpenAI's requirements
            #     fake_tool_response = {
            #         "type": "tool",
            #         "content": f"Error: {name} requires parameters but none were provided. This appears to be a technical issue with parameter parsing.",
            #         "tool_call_id": tool_call.get("id", ""),
            #         "name": name,
            #         "additional_kwargs": {},
            #         "response_metadata": {},
            #         "id": None
            #     }
                
            #     # Add the fake response to the state
            #     state["messages"].append(fake_tool_response)
                
            #     return "provide_fallback_response"
    
    # Anti-infinite loop protection: count recent tool calls
    recent_tool_calls = 0
    recent_empty_args = 0
    
    for msg in reversed(state["messages"][-15:]):  # Check last 15 messages
        if isinstance(msg, dict):
            if msg.get("tool_calls"):
                tool_calls_in_msg = msg.get("tool_calls", [])
                recent_tool_calls += len(tool_calls_in_msg)
                # Count empty args
                for tc in tool_calls_in_msg:
                    if not tc.get("args", {}):
                        recent_empty_args += 1
        else:
            if getattr(msg, 'tool_calls', []):
                tool_calls_in_msg = getattr(msg, 'tool_calls', [])
                recent_tool_calls += len(tool_calls_in_msg)
                # Count empty args
                for tc in tool_calls_in_msg:
                    if not tc.get("args", {}):
                        recent_empty_args += 1
    
    print(f"🔧 Recent tool calls in last 15 messages: {recent_tool_calls}")
    print(f"🔧 Recent empty args tool calls: {recent_empty_args}")
    
    # If too many recent tool calls OR too many empty args, force END
    # if recent_tool_calls > 6 or recent_empty_args > 3:
    #     print("🔧 TOO MANY TOOL CALLS OR EMPTY ARGS - Forcing fallback response")
    #     return "provide_fallback_response"
    
    if tool_calls:
        # Log each tool_call
        for i, tool_call in enumerate(tool_calls):
            print(f"🔧 Tool call {i}: {tool_call.get('name', 'unknown')} (id: {tool_call.get('id', 'no-id')})")
            print(f"🔧   Args: {tool_call.get('args', {})}")
            
        # Check authorization requirements
        for tool_call in tool_calls:
            if manager.requires_auth(tool_call["name"]):
                print(f"🔧 Routing to authorization for: {tool_call['name']}")
                return "authorization"
        
        print("🔧 Routing to tools")
        return "tools"
    
    print("🔧 Ending workflow (no tool calls)")
    return END

def get_tool_calls(message):
    """Extrae tool_calls de un mensaje, sea objeto o dict"""
    if isinstance(message, dict):
        return message.get("tool_calls", [])
    else:
        return getattr(message, 'tool_calls', [])

def authorize(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    user_id = config["configurable"].get("user_id")
    
    last_message = state["messages"][-1]
    tool_calls = get_tool_calls(last_message)
    
    print(f"🔧 authorize - Processing {len(tool_calls)} tool calls")
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        if not manager.requires_auth(tool_name):
            continue
            
        print(f"🔧 Authorizing tool: {tool_name}")
        try:
            auth_response = manager.authorize(tool_name, user_id)
            if auth_response.status != "completed":
                print(f"\nAuthorization required for {tool_name}\n")
                print(f"Visit the following URL to authorize:\n{auth_response.url}\n")
                print("Waiting for authorization...\n")

                manager.wait_for_auth(auth_response.id)
                if not manager.is_authorized(auth_response.id):
                    raise ValueError(f"Authorization failed for {tool_name}")
                    
        except Exception as e:
            print(f"🔧 Authorization error for {tool_name}: {e}")
            raise e

    print("🔧 Authorization completed")
    return {"messages": []}

def serialize_message(message):
    """Serializa cualquier tipo de mensaje de LangChain"""
    if hasattr(message, 'type') or isinstance(message, BaseMessage):
        # Para AIMessage, HumanMessage, ToolMessage, etc.
        return {
            "type": getattr(message, 'type', 'unknown'),
            "content": getattr(message, 'content', ''),
            "additional_kwargs": getattr(message, 'additional_kwargs', {}),
            "response_metadata": getattr(message, 'response_metadata', {}),
            "id": getattr(message, 'id', None),
            "tool_calls": getattr(message, 'tool_calls', []),
            "usage_metadata": getattr(message, 'usage_metadata', {}),
            "tool_call_id": getattr(message, 'tool_call_id', None),  # Para ToolMessage
            "name": getattr(message, 'name', None),  # Para ToolMessage
        }
    else:
        # Si ya es un dict, devolverlo tal como está
        return message

def serialize_tool_node(state):
    """ToolNode wrapper que serializa automáticamente los ToolMessage"""
    print("🔧 tools_node - INPUT:", [type(msg) for msg in state["messages"]])
    
    # Verificar los tool_calls que necesitan respuesta
    last_message = state["messages"][-1]
    if isinstance(last_message, dict):
        tool_calls = last_message.get("tool_calls", [])
    else:
        tool_calls = getattr(last_message, 'tool_calls', [])
    
    print(f"🔧 Expected tool_calls: {[tc.get('id', 'no-id') for tc in tool_calls]}")
    
    # DEBUG: Imprimir detalles completos de los tool_calls
    for i, tool_call in enumerate(tool_calls):
        print(f"🔧 Tool call {i} details:")
        print(f"   - ID: {tool_call.get('id', 'NO_ID')}")
        print(f"   - Name: {tool_call.get('name', 'NO_NAME')}")
        print(f"   - Args: {tool_call.get('args', {})}")
        print(f"   - Full tool_call: {tool_call}")
    
    try:
        # Ejecutar el ToolNode original
        result = tool_node.invoke(state)
        
        print(f"🔧 ToolNode result keys: {result.keys()}")
        
        # Serializar todos los mensajes en el resultado
        if "messages" in result:
            serialized_messages = []
            for msg in result["messages"]:
                serialized_msg = serialize_message(msg)
                
                # Log específico para ToolMessage
                if serialized_msg.get("type") == "tool":
                    print(f"🔧 Tool response - ID: {serialized_msg.get('tool_call_id')}, Name: {serialized_msg.get('name')}")
                    print(f"🔧 Tool response content: {serialized_msg.get('content', '')[:200]}...")  # First 200 chars
                
                serialized_messages.append(serialized_msg)
            
            result["messages"] = serialized_messages
            
            print(f"🔧 tools_node - OUTPUT: {len(serialized_messages)} messages")
            return result
        else:
            print("🔧 ERROR: ToolNode didn't return messages")
            return {"messages": []}
            
    except Exception as e:
        print(f"🔧 ERROR in ToolNode: {e}")
        import traceback
        print(f"🔧 Full traceback: {traceback.format_exc()}")
        
        # Crear mensajes de error para cada tool_call
        error_messages = []
        for tool_call in tool_calls:
            error_msg = {
                "type": "tool",
                "content": f"Error executing tool: {str(e)}",
                "tool_call_id": tool_call.get("id", ""),
                "name": tool_call.get("name", "unknown"),
                "additional_kwargs": {},
                "response_metadata": {},
                "id": None
            }
            error_messages.append(error_msg)
        
def provide_fallback_response(state: MessagesState):
    """Provides a helpful response when tools fail due to empty arguments"""
    print("🔧 provide_fallback_response - Creating helpful response for user")
    
    fallback_message = {
        "type": "ai",
        "content": "I apologize, but I'm having trouble accessing the specific Gmail thread details due to a technical issue with parameter passing. Based on the emails I can see, it appears you want me to work with a specific email thread. Could you please provide more specific details about which email you'd like me to help with? For example:\n\n- The subject line of the email\n- The sender's email address\n- When the email was sent\n\nWith this information, I can better assist you with your Gmail-related task.",
        "additional_kwargs": {},
        "response_metadata": {},
        "id": None,
        "tool_calls": [],
        "usage_metadata": {}
    }
    
    return {"messages": [fallback_message]}

class KeyPayload(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=10, max_length=500)
    
    @field_validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'ollama']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @field_validator('api_key')
    def validate_api_key(cls, v):
        return sanitize_string(v, 500)

@app.get("/keys")
@limiter.limit("10/minute")
def list_keys(request: Request):
    data = load_keys()
    return {
        provider: list(models.keys())
        for provider, models in data.items()
    }

@app.post("/keys")
@limiter.limit("5/minute")
def add_key(request: Request, payload: KeyPayload):
    data = load_keys()
    provider = payload.provider
    model = payload.model

    if provider not in data:
        data[provider] = {}
    data[provider][model] = payload.api_key
    save_keys(data)
    return {"status": "saved"}

@app.delete("/keys/{provider}/{model}")
@limiter.limit("5/minute")
def delete_key(request: Request, provider: str, model: str):
    data = load_keys()
    if provider in data and model in data[provider]:
        del data[provider][model]
        if not data[provider]:
            del data[provider]
        save_keys(data)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Key not found")

class ValidateKeyPayload(BaseModel):
    apiKey: str = Field(..., min_length=10, max_length=500)
    
    @field_validator('apiKey')
    def validate_api_key(cls, v):
        return sanitize_string(v, 500)

@app.post('/keys/validate-keys')
@limiter.limit("3/minute")
def validateKeys(request: Request, payload: ValidateKeyPayload):
    openai.api_key = payload.apiKey
    try:
        openai.models.list()
        return {'Valid': True}
    except openai.AuthenticationError as e:
        raise HTTPException(status_code=404, detail=f'[APIKEY_ERROR]: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unexpected error:{str(e)}')

class ConfigRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    apiKey: Optional[str] = Field(None, max_length=500)
    
    @field_validator('thread_id')
    def validate_thread_id_format(cls, v):
        return validate_thread_id(v)
    
    @field_validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'ollama']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @field_validator('apiKey')
    def validate_api_key(cls, v):
        if v is not None:
            return sanitize_string(v, 500)
        return v
    
@app.post("/configure")
@limiter.limit("10/minute")
async def configure_model(request: Request, config: ConfigRequest):
    try:
        logger.info(f"Configuring model for thread {config.thread_id}, provider: {config.provider}, model: {config.model}")
        
        # Crear modelo dinámicamente
        if config.provider == "openai":
            if not config.apiKey:
                raise HTTPException(400, detail="API key is required for OpenAI provider")
            
            model = ChatOpenAI(
                model=config.model,
                temperature=0,
                max_tokens=4000,
                timeout=30,
                max_retries=2,
                api_key=config.apiKey,
            )
            
        elif config.provider == "ollama":
            model = ChatOllama(
                model=config.model,
                streaming=True,
                base_url=ollama_url,
            )
        else:
            raise HTTPException(400, detail="Unsupported provider")
    
    except Exception as e:
        logger.error(f"Error configuring model: {str(e)}")
        raise HTTPException(500, detail="Failed to configure model")
        
    # Crear el workflow con ese modelo
    model_with_tools = model.bind_tools(tools)
        
    async def call_agent(state: MessagesState, writer, config: RunnableConfig, *, store: BaseStore):
        messages = state["messages"]
        
        # Get user_id from config
        user_id = config["configurable"].get("user_id").replace(".", "")
        namespace = ("memories", user_id)
        
        # Search for relevant memories based on the last user message
        last_user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) or (hasattr(msg, 'type') and msg.type == "human") or (isinstance(msg, dict) and msg.get('type') == "human"):
                last_user_message = msg
                break
        
        # Retrieve memories if there's a user message
        memories_str = ""
        if last_user_message:
            content = last_user_message.content if hasattr(last_user_message, 'content') else last_user_message.get('content', '')
            memories = await store.asearch(namespace, query=str(content))
            if memories:
                memories_str = "\n".join([f"- {d.value['data']}" for d in memories])
        
        # Build system message with memories
        system_msg = f"""You are a helpful AI assistant with access to Gmail tools. 

IMPORTANT: When using Gmail tools, you MUST provide all required parameters:
- Gmail_GetThread requires thread_id parameter
- Gmail_SendEmail requires subject, body, and recipient parameters  
- Gmail_ReplyToEmail requires body and reply_to_message_id parameters

If you don't have the required information, ask the user for it instead of calling tools without parameters.

User memories:
{memories_str}""" if memories_str else """You are a helpful AI assistant with access to Gmail tools.

IMPORTANT: When using Gmail tools, you MUST provide all required parameters:
- Gmail_GetThread requires thread_id parameter
- Gmail_SendEmail requires subject, body, and recipient parameters
- Gmail_ReplyToEmail requires body and reply_to_message_id parameters

If you don't have the required information, ask the user for it instead of calling tools without parameters."""
        
        # Insert system message at the beginning if not already present
        messages_with_system = messages[:]
        has_system = False
        if messages:
            first_msg = messages[0]
            if isinstance(first_msg, SystemMessage) or (isinstance(first_msg, dict) and first_msg.get('type') == 'system'):
                has_system = True
        
        if not has_system:
            system_dict = {"type": "system", "content": system_msg}
            messages_with_system = [system_dict] + messages
        
        # Check if user wants to remember something
        if last_user_message and "remember" in str(last_user_message.content if hasattr(last_user_message, 'content') else last_user_message.get('content', '')).lower():
            # Extract what to remember
            content = str(last_user_message.content if hasattr(last_user_message, 'content') else last_user_message.get('content', ''))
            # Store the entire message as a memory
            await store.aput(namespace, str(uuid.uuid4()), {"data": content})
        
        # Count recent tool calls to avoid infinite loops
        recent_tool_calls = sum(1 for msg in messages[-5:] 
                               if (isinstance(msg, dict) and msg.get("tool_calls")) or 
                                  (hasattr(msg, 'tool_calls') and getattr(msg, 'tool_calls', [])))
        
        # Add instruction to stop making tool calls if too many recent ones
        if recent_tool_calls > 3:
            system_reminder = {
                "type": "system",
                "content": "You have made several tool calls recently. Only make additional tool calls if absolutely necessary. If the task is complete, provide a final response without tool calls."
            }
            messages_with_system.append(system_reminder)
        
        # If there are many empty args tool calls, provide specific guidance
        empty_args_count = sum(1 for msg in messages[-5:] 
                              if (isinstance(msg, dict) and msg.get("tool_calls") and 
                                  any(not tc.get("args", {}) for tc in msg.get("tool_calls", []))) or
                                 (hasattr(msg, 'tool_calls') and getattr(msg, 'tool_calls', []) and
                                  any(not tc.get("args", {}) for tc in getattr(msg, 'tool_calls', []))))
        
        if empty_args_count > 2:
            empty_args_reminder = {
                "type": "system", 
                "content": "IMPORTANT: You've been making tool calls without required parameters. If you need to get thread details, you must provide the thread_id parameter. If you cannot determine the correct parameters, provide a helpful response to the user explaining what information you need."
            }
            messages_with_system.append(empty_args_reminder)
        
        # Stream tokens using astream
        full_content = ""
        tool_calls = []
        
        print(f"🔧 call_agent - About to call model with {len(messages_with_system)} messages")
        
        async for chunk in model_with_tools.astream(messages_with_system):
            # Stream content tokens
            if chunk.content:
                writer(chunk.content)
                full_content += chunk.content
            
            # Accumulate tool calls
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                print(f"🔧 call_agent - Received tool_calls chunk: {len(chunk.tool_calls)} calls")
                
                # Filter out tool calls with empty name attribute
                valid_tool_calls = [tc for tc in chunk.tool_calls if tc.get("name", "").strip()]
                
                # DEBUG: Print tool call details
                for i, tc in enumerate(valid_tool_calls):
                    print(f"🔧 Tool call {i}:")
                    print(f"   - Name: {tc.get('name', 'NO_NAME')}")
                    print(f"   - ID: {tc.get('id', 'NO_ID')}")
                    print(f"   - Args: {tc.get('args', {})}")
                
                tool_calls.extend(valid_tool_calls)
        
        print(f"🔧 call_agent - Final: content_length={len(full_content)}, tool_calls={len(tool_calls)}")
        
        # Create the full response message with accumulated content and tool calls
        response = AIMessage(content=full_content, tool_calls=tool_calls)
        serialized_response = serialize_message(response)
        
        # DEBUG: Verify serialization preserved tool_calls
        print(f"🔧 call_agent - Serialized tool_calls: {len(serialized_response.get('tool_calls', []))}")
        
        # Return the updated message history
        return {"messages": [serialized_response]}
    
    workflow = StateGraph(state_schema=MessagesState)
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", serialize_tool_node)
    workflow.add_node("authorization", authorize)
    workflow.add_node("provide_fallback_response", provide_fallback_response)
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["authorization", "tools", "provide_fallback_response", END])
    workflow.add_edge("authorization", "tools")
    workflow.add_edge("tools", "agent")
    workflow.add_edge("provide_fallback_response", END)
    
    # Guardarlo en memoria
    workflow_store[config.thread_id] = workflow
    
    return {"message": f"Workflow configurado para {config.thread_id}"}

@app.get("/getModels")
@limiter.limit("20/minute")
def get_ollama_models(request: Request):
    try:
        logger.info("Fetching Ollama models")
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        response.raise_for_status()
        models = response.json()["models"]
        modelNames = [model["name"] for model in models]
        return modelNames
    except requests.RequestException as e:
        logger.error(f"Error fetching Ollama models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch Ollama models")

class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1, max_length=10000)
    
    @field_validator('thread_id')
    def validate_thread_id_format(cls, v):
        return validate_thread_id(v)
    
    @field_validator('prompt')
    def validate_prompt(cls, v):
        return sanitize_string(v, max_prompt_length)         
                 
@app.post("/chat")
@limiter.limit("30/minute")
def chat_model(request: Request, chat_request: ChatRequest):
    try:
        logger.info(f"Chat request for thread {chat_request.thread_id}")
        
        config = {"configurable": {"thread_id": chat_request.thread_id, "user_id": email}}

        input_messages = [{
            "type": "human", 
            "content": chat_request.prompt
        }]        
        if chat_request.thread_id not in workflow_store:
            raise HTTPException(400, detail="Model not configured for this thread")
        
            
        return StreamingResponse(
            generate_response(chat_request.thread_id, input_messages, config), 
            media_type="text/event-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(500, detail="Internal server error")
    
async def generate_response(thread_id, input_messages, config):
    """Generate streaming response from the workflow"""
    async with (
        AsyncPostgresStore.from_conn_string(database_url) as store,
        AsyncPostgresSaver.from_conn_string(database_url) as checkpointer,
    ):        
        # Add recursion limit to prevent infinite loops
        config_with_limit = {
            **config,
            "recursion_limit": 50  # Increase from default 25
        }
        
        workflow_app = workflow_store[thread_id].compile(checkpointer=checkpointer, store=store)
        
        logger.info(f"Generating response for thread {thread_id}")
        
        try:
            async for chunk, metadata in workflow_app.astream(
                {"messages": input_messages},
                config_with_limit,  # Use config with recursion limit
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessage):
                    content = str(chunk.content) if chunk.content else ""
                    if content:
                        # Handle encoding issues
                        yield content.encode('utf-8', errors='ignore').decode('utf-8')
                        
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error for thread {thread_id}: {str(e)}")
            yield f"[ERROR] Authentication failed: {str(e)}"
        except Exception as e:
            print(f"ERROR: {e}")
            logger.error(f"Error generating response for thread {thread_id}: {str(e)}")
            yield f"[ERROR] Internal server error: {str(e)}"

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "LocalAI Chat API", "docs": "/docs"}