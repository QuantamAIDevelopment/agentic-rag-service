"""PostgreSQL HNSW vector store with optimizations."""

import asyncpg
import numpy as np
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from app.config.settings import settings

class PostgreSQLVectorStore:
    def __init__(self, store_name: str):
        self.store_name = store_name
        self.table_name = f"embeddings_{store_name}"
        self.index_name = f"hnsw_idx_{store_name}"
        self._pool: Optional[asyncpg.Pool] = None
        
    async def _get_pool(self):
        """Get connection pool for better performance."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
        return self._pool
        
    async def _get_connection(self):
        """Get database connection from pool."""
        pool = await self._get_pool()
        return await pool.acquire()
        
    async def create_store(self) -> None:
        """Create vector store table and HNSW index."""
        conn = await self._get_connection()
        try:
            await conn.execute(f"""
                CREATE EXTENSION IF NOT EXISTS vector;
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector(1024),
                    metadata JSONB DEFAULT '{{}}'
                )
            """)
            await self.create_hnsw_index()
            print(f"Vector store ready: {self.table_name}")
        finally:
            await conn.close()
        
    async def create_hnsw_index(self) -> None:
        """Create optimized HNSW index for vector similarity search."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                # Create HNSW index with optimized parameters
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.index_name} 
                    ON {self.table_name} 
                    USING hnsw (embedding vector_ip_ops) 
                    WITH (m = {settings.HNSW_M}, ef_construction = {settings.HNSW_EF_CONSTRUCTION})
                """)
                
                # Create additional indexes for metadata queries
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.store_name}_metadata_filename 
                    ON {self.table_name} USING BTREE ((metadata->>'filename'))
                """)
                
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.store_name}_content_text 
                    ON {self.table_name} USING GIN (to_tsvector('english', content))
                """)
                
                # Create unique constraint for duplicate prevention (handle existing duplicates)
                try:
                    await conn.execute(f"""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_{self.store_name}_unique_content 
                        ON {self.table_name} (content, (metadata->>'filename'))
                    """)
                except Exception as unique_error:
                    print(f"Unique index creation failed (duplicates exist): {unique_error}")
                    # Clean up duplicates and retry
                    await conn.execute(f"""
                        DELETE FROM {self.table_name} a USING {self.table_name} b 
                        WHERE a.id > b.id 
                        AND a.content = b.content 
                        AND a.metadata->>'filename' = b.metadata->>'filename'
                    """)
                    await conn.execute(f"""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_{self.store_name}_unique_content 
                        ON {self.table_name} (content, (metadata->>'filename'))
                    """)
                    print(f"Cleaned duplicates and created unique index")
                
            except Exception as e:
                print(f"Index creation failed: {e}")
                pass
        
    async def check_document_exists(self, filename: str) -> bool:
        """Check if document already exists in store."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                count = await conn.fetchval(f"""
                    SELECT COUNT(*) FROM {self.table_name} 
                    WHERE metadata->>'filename' = $1
                """, filename)
                return count > 0
            except Exception:
                return False
    
    async def insert_embeddings(self, embeddings: List[Dict[str, Any]]) -> None:
        """Optimized batch insert with duplicate prevention."""
        if not embeddings:
            return
            
        pool = await self._get_pool()
        conn = None
        try:
            conn = await pool.acquire()
            async with conn.transaction():
                # Prepare batch data
                batch_data = []
                for emb in embeddings:
                    embedding_vector = emb['embedding']
                    if isinstance(embedding_vector, np.ndarray):
                        vector_str = '[' + ','.join(map(str, embedding_vector.tolist())) + ']'
                    else:
                        vector_str = '[' + ','.join(map(str, embedding_vector)) + ']'
                    
                    metadata_json = json.dumps(emb.get('metadata', {}))
                    batch_data.append((emb['content'], vector_str, metadata_json))
                
                # Insert with conflict handling
                await conn.executemany(f"""
                    INSERT INTO {self.table_name} (content, embedding, metadata)
                    VALUES ($1, $2::vector, $3::jsonb)
                    ON CONFLICT DO NOTHING
                """, batch_data)
                
        except (asyncio.CancelledError, asyncio.TimeoutError):
            # Handle cancellation gracefully
            pass
        except Exception as e:
            print(f"Insert failed: {e}")
        finally:
            if conn:
                try:
                    await pool.release(conn)
                except (asyncio.CancelledError, Exception):
                    pass
        
    async def search(self, query_vector: np.ndarray, top_k: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Enhanced search with context window for better retrieval."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute(f"SET hnsw.ef_search = {settings.HNSW_EF_SEARCH}")
                
                if isinstance(query_vector, np.ndarray):
                    vector_list = query_vector.tolist()
                else:
                    vector_list = query_vector
                
                vector_str = '[' + ','.join(map(str, vector_list)) + ']'
                
                rows = await conn.fetch(f"""
                    SELECT content, (embedding <#> $1::vector) * -1 as similarity, metadata, id
                    FROM {self.table_name}
                    ORDER BY embedding <#> $1::vector
                    LIMIT $2 OFFSET $3
                """, vector_str, top_k, offset)
                
                results = []
                for row in rows:
                    metadata = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                    
                    # Get context window (surrounding lines)
                    context_content = await self._get_context_window(conn, row, metadata)
                    
                    results.append({
                        'content': context_content,
                        'original_content': row['content'],
                        'similarity': float(row['similarity']),
                        'metadata': metadata,
                        'id': row['id']
                    })
                return results
            except Exception as e:
                print(f"Search failed: {e}")
                return []
    
    async def _get_context_window(self, conn, row, metadata) -> str:
        """Get surrounding lines for better context."""
        try:
            filename = metadata.get('filename', '')
            line_number = metadata.get('line_number', 0)
            
            if not filename or not line_number:
                return row['content']
            
            # Get surrounding lines from same document
            window_size = settings.CONTEXT_WINDOW_SIZE
            context_rows = await conn.fetch(f"""
                SELECT content, metadata
                FROM {self.table_name}
                WHERE metadata->>'filename' = $1
                AND CAST(metadata->>'line_number' AS INTEGER) BETWEEN $2 AND $3
                ORDER BY CAST(metadata->>'line_number' AS INTEGER)
            """, filename, line_number - window_size, line_number + window_size)
            
            if context_rows:
                context_lines = [r['content'] for r in context_rows]
                full_context = ' '.join(context_lines)
                
                # Limit context length
                if len(full_context) > settings.MAX_CONTEXT_LENGTH:
                    full_context = full_context[:settings.MAX_CONTEXT_LENGTH] + '...'
                
                return full_context
            
            return row['content']
            
        except Exception as e:
            print(f"Context window failed: {e}")
            return row['content']
    
    async def get_total_count(self, query_vector: np.ndarray, threshold: float = 0.3) -> int:
        """Get total count of results above threshold."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                if isinstance(query_vector, np.ndarray):
                    vector_list = query_vector.tolist()
                else:
                    vector_list = query_vector
                
                vector_str = '[' + ','.join(map(str, vector_list)) + ']'
                
                count = await conn.fetchval(f"""
                    SELECT COUNT(*) FROM {self.table_name}
                    WHERE (embedding <#> $1::vector) * -1 > $2
                """, vector_str, threshold)
                
                return count or 0
            except Exception as e:
                print(f"Count query failed: {e}")
                return 0
        
    async def get_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
                return {
                    "store_name": self.store_name,
                    "total_vectors": count,
                    "table_name": self.table_name,
                    "index_name": self.index_name
                }
            except Exception as e:
                print(f"Stats query failed: {e}")
                return {
                    "store_name": self.store_name,
                    "total_vectors": 0,
                    "table_name": self.table_name,
                    "index_name": self.index_name
                }
    
    async def close(self):
        """Close connection pool gracefully."""
        if self._pool:
            try:
                await self._pool.close()
            except (asyncio.CancelledError, Exception):
                pass
            finally:
                self._pool = None
    
