"""Startup script for the Agentic RAG System."""

import uvicorn
import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Start the FastAPI server."""
    print("🚀 Starting Agentic RAG System...")
    print("📚 Intelligent document management with HNSW indexing")
    print("🔗 API Documentation: http://localhost:8000/docs")
    print("📊 Health Check: http://localhost:8000/health")
    print("\n" + "="*50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        print("Please check your configuration and dependencies.")

if __name__ == "__main__":
    main()