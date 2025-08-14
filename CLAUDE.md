# LocalAI Chat API Project

## Project Overview
This is a full-stack chat application that provides a secure interface for interacting with various LLM providers (OpenAI, Ollama, Anthropic, Google) with tool integration capabilities. The backend is built with FastAPI and the frontend uses Astro with React/TypeScript.

## Architecture
- **Backend**: FastAPI (Python) with LangGraph workflows
- **Frontend**: Astro with React/TypeScript components  
- **Database**: PostgreSQL (optional, for memory/persistence)
- **Tools**: LangChain Arcade for tool integrations
- **Containerization**: Docker support with docker-compose

## Backend Structure (`/backend/`)

### Main Application (`main.py`)
- FastAPI application with CORS and rate limiting
- Combined chat endpoint that auto-configures models on first request
- Support for multiple LLM providers through `ModelFactory`
- Workflow management using LangGraph `StateGraph`
- Tool integration with LangChain Arcade

### Key Components
- **Config Class**: Centralized configuration management
- **WorkflowManager**: Manages workflow instances per thread
- **ModelFactory**: Creates LLM instances for different providers  
- **WorkflowBuilder**: Builds LangGraph workflows with agent/tool nodes

### API Endpoints
- `POST /chat` - Combined chat with auto-configuration
- `POST /chat-legacy` - Legacy endpoint requiring pre-configuration
- `POST /configure` - Explicit model configuration
- `GET /models` - List available models by provider
- `GET /toolkits` - List available tool toolkits
- `GET /threads/{thread_id}/status` - Thread status
- `DELETE /threads/{thread_id}` - Delete thread
- `GET /health` - Health check

### Configuration Options
- **Providers**: OpenAI, Ollama, Anthropic, Google
- **Default Model**: llama3.2 (Ollama)
- **Tools**: Gmail, Slack, Calendar, Drive (via Arcade)
- **Memory**: PostgreSQL-based persistence (optional)

## Frontend Structure (`/frontend/src/`)

### Components
- **Chat Components** (`components/chat/`): Chat interface, input/output, history
- **Layout Components** (`components/layout/`): Sidebar, navigation, main layout
- **UI Components** (`components/ui/`): Reusable UI elements, toggles, tools list

### Hooks (`hooks/`)
- `useChatApi.ts` - Chat API integration
- `useApi.ts` - General API utilities
- `useChatHistoryContext.ts` - Chat history management

### Context
- `ChatHistoryContext.tsx` - Global chat state management

## Environment Variables

### Required for Backend
```bash
# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/localai

# Tool Integration
ARCADE_API_KEY=your_arcade_key

# User Identity
EMAIL=user@example.com

# Model Defaults
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=4000

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# CORS Configuration
CORS_ORIGINS=http://localhost:4322
```

### API Keys (provided per request)
- OpenAI: `api_key` in request body
- Anthropic: `api_key` in request body  
- Google: `api_key` in request body

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py  # or uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
bun install
bun run dev
```

### Docker
```bash
docker-compose up --build
```

## Testing
- Backend tests: `python backend/test.py`
- Check main.py:785-787 for uvicorn server setup

## Current Git Branch
- Main branch: `main`
- Current feature branch: `feature/ASL1_separating_tools`

## Recent Changes
- Combined configure and chat operations into single `/chat` endpoint
- Auto-configuration on first request with sensible defaults
- Maintained backward compatibility with `/chat-legacy` endpoint
- Added `CombinedChatRequest` model for flexible request handling

## Usage Examples

### First Request (Auto-Configure + Chat)
```json
POST /chat
{
  "thread_id": "user123",
  "prompt": "Hello!",
  "model": "gpt-4",
  "provider": "openai", 
  "api_key": "sk-...",
  "toolkits": ["Gmail"]
}
```

### Subsequent Requests
```json
POST /chat
{
  "thread_id": "user123",
  "prompt": "What's my latest email?"
}
```

## Security Notes
- Input sanitization with bleach
- Rate limiting on all endpoints
- CORS configuration
- No hardcoded API keys (passed per request)
- Thread ID validation and sanitization

## Tool Integration
- Uses LangChain Arcade for tool access
- Available toolkits: Gmail, Slack, Calendar, Drive
- OAuth-based authorization for tools
- Anti-infinite loop protection for tool calls

## Known Limitations
- PostgreSQL required for memory persistence
- Tool authorization requires manual OAuth flow
- Default Ollama model assumes local installation