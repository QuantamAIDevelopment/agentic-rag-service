"""Chat and memory data models."""

from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    created_at: datetime
    updated_at: datetime

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: Optional[str] = None
    feedback_type: FeedbackType
    comment: Optional[str] = None
    rating: Optional[int] = None  # 1-5 scale

class ChatRequest(BaseModel):
    query: str
    # session_id: Optional[str] = None  # Commented out
    response_format: str = "concise"