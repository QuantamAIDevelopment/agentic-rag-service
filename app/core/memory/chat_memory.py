"""Chat memory management with PostgreSQL storage."""

import asyncpg
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config.settings import settings
from app.models.chat import ChatMessage, ChatSession, FeedbackRequest

class ChatMemoryManager:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=5)
        return self._pool
    
    async def create_tables(self):
        """Create chat memory tables."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS chat_feedback (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
                    message_id INTEGER REFERENCES chat_messages(id),
                    feedback_type VARCHAR(50) NOT NULL,
                    comment TEXT,
                    rating INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_chat_feedback_session ON chat_feedback(session_id);
            """)
    
    async def create_session(self) -> str:
        """Create new chat session."""
        session_id = str(uuid.uuid4())
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO chat_sessions (session_id) VALUES ($1)",
                session_id
            )
        return session_id
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> int:
        """Add message to session."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Ensure session exists
            await conn.execute(
                "INSERT INTO chat_sessions (session_id) VALUES ($1) ON CONFLICT DO NOTHING",
                session_id
            )
            
            message_id = await conn.fetchval(
                "INSERT INTO chat_messages (session_id, role, content, metadata) VALUES ($1, $2, $3, $4) RETURNING id",
                session_id, role, content, json.dumps(metadata or {})
            )
            
            # Update session timestamp
            await conn.execute(
                "UPDATE chat_sessions SET updated_at = NOW() WHERE session_id = $1",
                session_id
            )
            
            return message_id
    
    async def get_session_context(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages for context."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role, content, timestamp, metadata FROM chat_messages WHERE session_id = $1 ORDER BY timestamp DESC LIMIT $2",
                session_id, limit
            )
            
            messages = []
            for row in reversed(rows):  # Reverse to get chronological order
                messages.append(ChatMessage(
                    role=row['role'],
                    content=row['content'],
                    timestamp=row['timestamp'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ))
            
            return messages
    
    async def add_feedback(self, feedback: FeedbackRequest) -> None:
        """Store user feedback."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO chat_feedback (session_id, message_id, feedback_type, comment, rating) VALUES ($1, $2, $3, $4, $5)",
                feedback.session_id, feedback.message_id, feedback.feedback_type.value, feedback.comment, feedback.rating
            )
    
    async def get_feedback_insights(self) -> Dict[str, Any]:
        """Get aggregated feedback for improvement."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            total_feedback = await conn.fetchval("SELECT COUNT(*) FROM chat_feedback")
            avg_rating = await conn.fetchval("SELECT AVG(rating) FROM chat_feedback WHERE rating IS NOT NULL")
            
            feedback_dist = await conn.fetch(
                "SELECT feedback_type, COUNT(*) as count FROM chat_feedback GROUP BY feedback_type"
            )
            
            return {
                "total_feedback": total_feedback or 0,
                "avg_rating": float(avg_rating) if avg_rating else 0.0,
                "feedback_distribution": {row['feedback_type']: row['count'] for row in feedback_dist}
            }
    
    async def get_session_list(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent chat sessions."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT session_id, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT $1",
                limit
            )
            return [dict(row) for row in rows]
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete chat session and all messages."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM chat_feedback WHERE session_id = $1", session_id)
                await conn.execute("DELETE FROM chat_messages WHERE session_id = $1", session_id)
                result = await conn.execute("DELETE FROM chat_sessions WHERE session_id = $1", session_id)
                return "DELETE 1" in result
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

chat_memory = ChatMemoryManager()