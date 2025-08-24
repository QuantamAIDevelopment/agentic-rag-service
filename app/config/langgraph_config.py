"""LangGraph and LangChain configuration."""

from pydantic_settings import BaseSettings
from typing import Dict, Any

class LangGraphConfig(BaseSettings):
    """Configuration for LangGraph workflows and agents."""
    
    # LLM Configuration
    AZURE_PHI4_ENDPOINT: str = ""
    AZURE_PHI4_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Embedding Model
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    
    # Confidence Thresholds
    PHI4_CONFIDENCE_THRESHOLD: float = 0.75
    ROUTING_CONFIDENCE_THRESHOLD: float = 0.85
    
    # Single Vector Store for All Documents
    VECTOR_STORES: Dict[str, Any] = {
        "documents": {"priority": 1, "description": "All documents - land development, policies, procedures"}
    }
    
    # HNSW Parameters
    HNSW_M: int = 16
    HNSW_EF_CONSTRUCTION: int = 200
    HNSW_EF_SEARCH: int = 100
    
    # Agent Configuration
    MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        extra = "allow"

# Global configuration
langgraph_config = LangGraphConfig()