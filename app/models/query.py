"""Query data models."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryResponse(BaseModel):
    query: str
    answer: str
    precise_answer: str
    process_time: float
    query_count: int
    sources: List[Dict[str, Any]] = []
    total_results: int = 0
    suggestions: List[str] = []
    # session_id: Optional[str] = None  # Commented out
    # message_id: Optional[int] = None   # Commented out