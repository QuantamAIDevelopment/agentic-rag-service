"""Embedding data models."""

from pydantic import BaseModel
from typing import List, Dict, Any

class EmbeddingModel(BaseModel):
    id: str
    text: str
    embedding: List[float]  # numpy array as list for JSON serialization
    metadata: Dict[str, Any] = {}
    store_name: str
    
class VectorStoreModel(BaseModel):
    name: str
    description: str
    embedding_dimension: int = 1024
    total_vectors: int = 0
    index_type: str = "hnsw"
    configuration: Dict[str, Any] = {}