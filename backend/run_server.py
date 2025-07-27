#!/usr/bin/env python3
"""
Simple script to run the FastAPI server with proper environment setup.
This helps test compatibility with the existing main.py
"""

import os
import sys
import uvicorn
from pathlib import Path

def setup_environment():
    """Setup environment variables for testing."""
    # Set development environment
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DEBUG", "true")
    
    # Database settings
    os.environ.setdefault("DB_URL", "sqlite:///./data/dev.db")
    
    # CORS settings  
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:4321,http://localhost:3000")
    
    # Ollama settings
    os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
    
    print("🔧 Environment configured for development")

def check_requirements():
    """Check if required directories exist."""
    required_dirs = ["config", "data", "logs"]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"📁 Created directory: {dir_name}")

def main():
    """Run the development server."""
    print("🚀 Starting LocalAI Development Server")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    check_requirements()
    
    # Import and test new architecture
    try:
        from config.settings import settings
        print(f"✅ Configuration loaded: {settings.app_name}")
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Database: {settings.database.url}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Test database
    try:
        from database import create_tables
        create_tables()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    
    print("\n🌐 Starting server at http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("\n" + "=" * 50)
    
    # Run the server
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()