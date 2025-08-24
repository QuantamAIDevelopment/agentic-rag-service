"""Document data models."""

from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentFormat(Enum):
    PDF = "pdf"
    DOCX = "docx"  
    TXT = "txt"
    MD = "md"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(BaseModel):
    id: Optional[str] = None
    filename: str
    format: DocumentFormat
    content: str
    metadata: Dict[str, Any] = {}
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    message: str