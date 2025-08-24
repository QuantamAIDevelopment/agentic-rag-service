"""LangGraph Agentic RAG System."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.api.v1.router import api_router
from app.core.startup import startup_handler

app = FastAPI(title="LangGraph Agentic RAG", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    """Initialize vector stores on startup."""
    startup_handler()

@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown - close database connections."""
    try:
        from app.core.vector_store.store_manager import store_manager
        await store_manager.close_all_stores()
    except Exception:
        pass

@app.get("/")
async def root():
    return {"framework": "LangGraph + LangChain", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)