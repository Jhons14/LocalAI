# 🧠 LLM Chat Interface

A professional open-source application for seamlessly interacting with Large Language Models (LLMs), supporting both local models via [Ollama](https://ollama.com/) and cloud-based models through OpenAI's ChatGPT API.

## ✨ Features

- 🏠 **Local LLM Support** - Compatible with Ollama for privacy-focused AI interactions
- ☁️ **Cloud Integration** - OpenAI ChatGPT API support with secure key management
- ⚡ **Modern Frontend** - Built with Astro, React, and Tailwind CSS
- 🚀 **Robust Backend** - FastAPI-powered Python backend with LangChain integration
- 🔐 **Security First** - Secure API key management and CORS protection
- 💬 **Interactive Chat** - Real-time chat interface with conversation history
- 📱 **Responsive Design** - Mobile-friendly UI with modern components
- 🐳 **Docker Ready** - Complete containerization support for easy deployment

## 🏗️ Tech Stack

| Component  | Technologies                          |
| ---------- | ------------------------------------- |
| Frontend   | Astro, React 19, Tailwind CSS 4.0     |
| Backend    | Python, FastAPI, LangChain            |
| UI Library | Radix UI, Lucide Icons, Framer Motion |
| Local LLM  | Ollama                                |
| Cloud LLM  | OpenAI API (ChatGPT)                  |
| Deployment | Docker, Docker Compose                |

## 🚀 Quick Start

### Prerequisites

- Node.js (v18+)
- Python (v3.8+)
- Git
- Docker & Docker Compose (optional)

### Option 1: Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/Jhons14/LocalAI.git
cd LocalAI
```

#### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory with your configuration:

```env
# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# CORS Settings
ALLOWED_ORIGINS=http://localhost:4321,http://localhost:3000
```

Start the backend server:

```bash
# From backend directory
python -m uvicorn main:app --reload --port 8000
```

#### 3. Frontend Setup

Open a new terminal and navigate to the frontend:

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:

- Frontend: `http://localhost:4321`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### Option 2: Docker Deployment

For a complete containerized setup:

```bash
# Clone the repository
git clone https://github.com/Jhons14/LocalAI.git
cd LocalAI

# Build and start all services
docker-compose up --build
```

## 🛠️ Configuration

### Local LLM Setup (Ollama)

1. Install [Ollama](https://ollama.com/) on your system
2. Pull your desired model:
   ```bash
   ollama pull llama2
   # or
   ollama pull codellama
   ```
3. Ensure Ollama is running on `http://localhost:11434`

### OpenAI API Setup

1. Get your API key from [OpenAI](https://platform.openai.com/)
2. Add it to your `.env` file in the backend directory
3. The application will automatically detect and use the API key

## 🔧 Environment Variables

The application supports the following environment variables:

### Backend (.env in backend directory)

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# CORS Settings
ALLOWED_ORIGINS=http://localhost:4321,http://localhost:3000

# Optional: Custom port
PORT=8000
```

## 🔒 Security

- **API Key Protection** - OpenAI API keys are never exposed to the frontend
- **CORS Configuration** - Properly configured Cross-Origin Resource Sharing
- **Environment Isolation** - Sensitive data managed through environment variables
- **Production Ready** - HTTPS support and security headers for production deployments

## 📚 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation powered by FastAPI's automatic OpenAPI generation.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🛣️ Roadmap

- [ ] User authentication and authorization
- [ ] Persistent chat history with database storage
- [ ] Multi-model support with real-time switching
- [ ] File upload and document analysis capabilities
- [ ] Voice input and text-to-speech output
- [ ] Conversation templates and presets
- [ ] Export chat conversations
- [ ] Admin dashboard for usage analytics

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Jhon Steven Orjuela**

- Website: [jstevenon.com](https://www.jstevenon.com/)
- GitHub: [@Jhons14](https://github.com/Jhons14)

---

⭐ If you found this project helpful, please consider giving it a star on GitHub!
