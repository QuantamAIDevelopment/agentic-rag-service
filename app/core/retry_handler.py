"""Retry mechanism for database operations."""

import asyncio
import functools
from typing import Callable, Any, Optional

def retry_async(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for async functions with retry logic."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    
                    wait_time = delay * (backoff ** attempt)
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

class DatabaseRetryHandler:
    @staticmethod
    @retry_async(max_retries=3, delay=1.0)
    async def execute_with_retry(conn, query: str, *args):
        """Execute database query with retry logic."""
        return await conn.execute(query, *args)
    
    @staticmethod
    @retry_async(max_retries=3, delay=1.0)
    async def fetch_with_retry(conn, query: str, *args):
        """Fetch database results with retry logic."""
        return await conn.fetch(query, *args)
    
    @staticmethod
    @retry_async(max_retries=3, delay=1.0)
    async def fetchval_with_retry(conn, query: str, *args):
        """Fetch single value with retry logic."""
        return await conn.fetchval(query, *args)

db_retry = DatabaseRetryHandler()