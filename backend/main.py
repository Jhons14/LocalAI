
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from fastapi import HTTPException
from dotenv import load_dotenv
from typing import Any
import openai
from openai import AuthenticationError
from pathlib import Path


load_dotenv()

workflow_store: dict[str, Any] = {}
memory_store: dict[str, MemorySaver] = {}

origins = [
    "http://localhost:4321",
]

app = FastAPI()

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

class KeyPayload(BaseModel):
    provider: str
    model: str
    api_key: str

@app.get("/keys")
def list_keys():
    data = load_keys()
    return {
        provider: list(models.keys())
        for provider, models in data.items()
    }

@app.post("/keys")
def add_key(payload: KeyPayload):
    data = load_keys()
    provider = payload.provider
    model = payload.model

    if provider not in data:
        data[provider] = {}
    data[provider][model] = payload.api_key
    save_keys(data)
    return {"status": "saved"}


@app.delete("/keys/{provider}/{model}")
def delete_key(provider: str, model: str):
    data = load_keys()
    if provider in data and model in data[provider]:
        del data[provider][model]
        if not data[provider]:
            del data[provider]
        save_keys(data)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Key not found")

class ValidateKeyPayload(BaseModel):
    apiKey: str

@app.post('/keys/validate-keys')
def validateKeys (payload:ValidateKeyPayload):
    openai.api_key = payload.apiKey
    print(payload.apiKey)
    try:
        openai.models.list()
        return {'Valid': True}
    except AuthenticationError as e:
        raise HTTPException(status_code=404, detail=f'[APIKEY_ERROR]: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unexpected error:{str(e)}')


class ConfigRequest(BaseModel):
    thread_id: str
    model: str  # 'gpt-4o' o 'qwen2.5:3b'
    provider: str  # 'openai' o 'ollama'
    
@app.post("/configure")
def configure_model(config: ConfigRequest):
    # Obtener o crear memoria por thread
    memory = memory_store.setdefault(config.thread_id, MemorySaver())
    
    # # Crear modelo dinámicamente
    if config.provider == "openai":
        keys = load_keys()
        if config.provider not in keys:
            raise HTTPException(400, detail=f"No se cuenta con llaves para el proveedor {config.provider}")
        if config.model not in keys[config.provider]:
            raise HTTPException(400, detail=f"No se cuenta con llaves para el modelo {config.model}")
        openAIApi_key = keys[config.provider][config.model]

        model = ChatOpenAI(
            model=config.model,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=openAIApi_key,  # if you prefer to pass api key in directly instaed of using env vars
            # base_url="...",
            # organization="...",
            # other params...
        )
        
    if config.provider == "ollama":
        
        model = ChatOllama(
            model = config.model,
            streaming=True
            # other params ...
        )   
        
    else:
        raise HTTPException(400, detail="Proveedor no soportado")
    # Crear el workflow con ese modelo
    def call_model(state: dict):
        return {"messages": model.invoke(state["messages"])}
    
    workflow = StateGraph(state_schema=MessagesState)
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")
    workflow_app = workflow.compile(checkpointer=memory)
    # # Guardarlo en memoria
    workflow_store[config.thread_id] = workflow_app
    return {"message": f"Workflow configurado para {config.thread_id}"}

@app.get("/getModels")
def get_ollama_models():
    response = requests.get("http://localhost:11434/api/tags")
    models = response.json()["models"]

    modelNames = []
    for model in models:
        modelNames.append(model["name"])
    return modelNames


class ChatRequest(BaseModel):
    thread_id: str
    prompt: str                      
@app.post("/chat")
async def chat_model(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    input_messages = [HumanMessage(request.prompt)]
    
    try:
        workflow_store[request.thread_id]
    except:
        raise HTTPException(400, detail="No se ha configurado el modelo para este thread.")

    return StreamingResponse(
        generate_response(request.thread_id,input_messages, config), 
        media_type="text/event-stream",
    )
    
def generate_response(thread_id,input_messages, config):
    # Call the workflow with the input messages and config    
    workflow_app = workflow_store[thread_id]
    buffer = "" 
    try:
        for chunk, metadata in workflow_app.stream(
            {"messages": input_messages},
            config,
            # highlight-next-line
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage):  # Filter to just model responses
                yield chunk.content
                
        if buffer:
            yield buffer
            buffer = ""  # Reset buffer after sending a complete message
    except AuthenticationError as e:
        yield f"[ERROR] Error de OpenAI: {e}"
    except Exception as e:
        yield f"[ERROR] Error interno del servidor: {e}"    