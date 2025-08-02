
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
from langchain_core.messages import HumanMessage, AIMessage

from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from pydantic import BaseModel, field_validator, Field
from typing import Any, Optional
import openai
from pathlib import Path
import os
import bleach
from dotenv import load_dotenv

load_dotenv()


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

workflow_store: dict[str, Any] = {}
memory_store: dict[str, MemorySaver] = {}

manager = ToolManager(api_key=arcade_api_key)

manager.init_tools(toolkits=["Gmail"])

tools = manager.to_langchain(use_interrupts=True)


tool_node = ToolNode(tools)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)


# CORS origins validation
origins_str = os.getenv("CORS_ORIGINS", "http://localhost:4322")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

app = FastAPI(
    title="LocalAI Chat API",
    description="Secure chat interface for LLM models",
    version="1.0.0"
)

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
def configure_model(request: Request, config: ConfigRequest):
    try:
        logger.info(f"Configuring model for thread {config.thread_id}, provider: {config.provider}, model: {config.model}")
        
        # Obtener o crear memoria por thread
        memory = memory_store.setdefault(config.thread_id, MemorySaver())
        
        # Crear modelo dinámicamente
        if config.provider == "openai":
            if not config.apiKey:
                raise HTTPException(400, detail="API key is required for OpenAI provider")
            
            model = ChatOpenAI(
                model=config.model,
                temperature=0,
                max_tokens=4000,  # Set reasonable limit
                timeout=30,       # 30 second timeout
                max_retries=2,
                api_key=config.apiKey,
            )
            
        elif config.provider == "ollama":
            model = ChatOllama(
                model=config.model,
                streaming=True,
                base_url=ollama_url,
                timeout=30,
            )
            
        else:
            raise HTTPException(400, detail="Unsupported provider")
    
    except Exception as e:
        logger.error(f"Error configuring model: {str(e)}")
        raise HTTPException(500, detail="Failed to configure model")
    # Crear el workflow con ese modelo
    model_with_tools = model.bind_tools(tools)
       
    def call_model(state: dict):        
        return {"messages": model_with_tools.invoke(state["messages"])}
    
    workflow = StateGraph(state_schema=MessagesState)
    workflow.add_node("model", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "model")
    workflow_app = workflow.compile(checkpointer=memory)
    # # Guardarlo en memoria
    workflow_store[config.thread_id] = workflow_app
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
async def chat_model(request: Request, chat_request: ChatRequest):
    try:
        logger.info(f"Chat request for thread {chat_request.thread_id}")
        
        config = {"configurable": {"thread_id": chat_request.thread_id}}
        input_messages = [HumanMessage(chat_request.prompt)]
        
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
    
def generate_response(thread_id, input_messages, config):
    """Generate streaming response from the workflow"""
    workflow_app = workflow_store[thread_id]
    buffer = ""
    
    try:
        logger.info(f"Generating response for thread {thread_id}")
        
        for chunk, metadata in workflow_app.stream(
            {"messages": input_messages},
            config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage):
                content = chunk.content
                if content:  # Only yield non-empty content
                    yield content
                
        if buffer:
            yield buffer
            
    except openai.AuthenticationError as e:
        logger.error(f"OpenAI authentication error for thread {thread_id}: {str(e)}")
        yield f"[ERROR] Authentication failed: {str(e)}"
    except Exception as e:
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