"""Application settings."""

from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # Database Components
    DB_HOST: str = "agentic-rag-server.postgres.database.azure.com"
    DB_PORT: int = 5432
    DB_USER: str = "ai_db_admin"
    DB_PASSWORD: str = "QAID@2025"
    DB_NAME: str = "agentic_rag_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """Build database URL with proper encoding for special characters."""
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"postgresql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # BGE-3 Configuration  
    BGE_MODEL_NAME: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DIMENSION: int = 1024
    BATCH_SIZE: int = 64
    
    # HNSW Parameters
    HNSW_M: int = 16
    HNSW_EF_CONSTRUCTION: int = 200
    HNSW_EF_SEARCH: int = 100
    
    # LLM Configuration (Phi-4 primary, OpenAI backup)
    AZURE_AI_ENDPOINT: str = ""
    AZURE_AI_API_KEY: str = ""
    AZURE_AI_API_VERSION: str = "2024-05-01-preview"
    OPENAI_API_KEY: str = ""
    
    # Performance & Search
    CONFIDENCE_THRESHOLD: float = 0.85
    MAX_RESULTS: int = 50
    BATCH_SIZE_UPLOAD: int = 50
    BATCH_SIZE_EMBEDDING: int = 32
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 25
    MAX_PAGE_SIZE: int = 100
    
    # Legal Document Thresholds
    LEGAL_HIGH_PRECISION: float = 0.4
    LEGAL_MEDIUM_PRECISION: float = 0.3
    LEGAL_MINIMUM: float = 0.25
    
    # Context Window Settings
    CONTEXT_WINDOW_SIZE: int = 3  # Lines before/after for context
    MAX_CONTEXT_LENGTH: int = 2000  # Max characters in context
    

    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()