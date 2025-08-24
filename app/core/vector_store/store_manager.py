"""Vector Store Manager for automatic department store creation and routing."""

import asyncio
from typing import Dict, List, Any
from app.config.langgraph_config import langgraph_config
from app.core.vector_store.postgresql_store import PostgreSQLVectorStore

class VectorStoreManager:
    def __init__(self):
        self.stores: Dict[str, PostgreSQLVectorStore] = {}
        self.department_keywords = self._build_department_keywords()
    
    def _build_department_keywords(self) -> Dict[str, List[str]]:
        """Single store for all documents."""
        return {
            "documents": ["all", "documents", "content"]
        }
    
    async def initialize_all_stores(self):
        """Create single document vector store automatically."""
        # print("Initializing document vector store...")  # Reduce logs
        
        for dept_name, config in langgraph_config.VECTOR_STORES.items():
            # print(f"Creating vector store: {dept_name}")  # Reduce logs
            store = PostgreSQLVectorStore(dept_name)
            await store.create_store()
            self.stores[dept_name] = store
            # print(f"Created {dept_name}: {config['description']}")  # Reduce logs
        
        print(f"Vector stores ready: {len(self.stores)}")
    
    def route_to_department(self, content: str, filename: str = "") -> str:
        """Route all content to single documents store."""
        return "documents"  # Always use single store
    
    def get_store(self, department: str) -> PostgreSQLVectorStore:
        """Get vector store for specific department."""
        return self.stores.get(department, self.stores["documents"])
    
    def get_all_departments(self) -> List[str]:
        """Get list of all available land development stores."""
        return list(langgraph_config.VECTOR_STORES.keys())
    
    def add_department(self, dept_name: str, description: str, keywords: List[str]):
        """Add new land development store (for future expansion)."""
        # This method allows adding new stores with one line
        langgraph_config.VECTOR_STORES[dept_name] = {
            "priority": len(langgraph_config.VECTOR_STORES) + 1,
            "description": description
        }
        self.department_keywords[dept_name] = keywords
    
    async def close_all_stores(self):
        """Close all database connections gracefully."""
        for store in self.stores.values():
            try:
                await store.close()
            except Exception:
                pass
        self.stores.clear()

# Global store manager
store_manager = VectorStoreManager()