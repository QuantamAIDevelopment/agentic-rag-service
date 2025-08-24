"""LangGraph Document Agent."""

import os
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from app.core.embeddings.bge3_generator import bge3_generator
from pydantic import BaseModel

class DocumentState(BaseModel):
    file_path: str
    vector_store: str = ""
    status: str = "pending"

class DocumentProcessingAgent:
    def __init__(self):
        self.phi4_llm = None
        self.backup_llm = None
        self.embeddings = bge3_generator
        self.graph = self._build_graph()
    
    def _get_llm(self):
        """Get LLM with Phi-4 primary, OpenAI backup."""
        try:
            if self.phi4_llm is None:
                from langchain_openai import AzureChatOpenAI
                self.phi4_llm = AzureChatOpenAI(
                    model="phi-4",
                    temperature=0.1,
                    azure_endpoint=os.getenv("AZURE_AI_ENDPOINT"),
                    api_key=os.getenv("AZURE_AI_API_KEY"),
                    api_version=os.getenv("AZURE_AI_API_VERSION")
                )
            return self.phi4_llm
        except Exception:
            if self.backup_llm is None:
                self.backup_llm = ChatOpenAI(
                    model="gpt-4o-mini", 
                    temperature=0.1,
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            return self.backup_llm
    
    def _build_graph(self):
        workflow = StateGraph(DocumentState)
        
        workflow.add_node("classify", self._classify_content)
        workflow.add_node("process", self._process_document)
        
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "process")
        workflow.add_edge("process", END)
        
        return workflow.compile()
    
    def _classify_content(self, state: DocumentState):
        # Use store manager for intelligent land development routing
        from app.core.vector_store.store_manager import store_manager
        
        # Route to appropriate land development store
        department = store_manager.route_to_department("", state.file_path)
        state.vector_store = department
        return state
    
    async def _process_document(self, state: DocumentState):
        try:
            # Parse document content
            from app.core.document.parser import DocumentParser
            from app.core.vector_store.store_manager import store_manager
            
            parser = DocumentParser()
            lines = parser.parse_document(state.file_path)
            
            # Generate embeddings and store
            store = store_manager.get_store(state.vector_store)
            embeddings_data = []
            
            for i, line in enumerate(lines[:10]):  # Limit to first 10 lines for now
                if line.strip():
                    embedding = self.embeddings.generate_single_embedding(line)
                    embeddings_data.append({
                        'content': line,
                        'embedding': embedding.tolist(),
                        'metadata': {'line_number': i, 'filename': state.file_path}
                    })
            
            if embeddings_data:
                await store.insert_embeddings(embeddings_data)
                state.status = "completed"
            else:
                state.status = "failed"
                
        except Exception as e:
            state.status = "failed"
            print(f"Document processing error: {e}")
            
        return state
    
    async def process_document(self, file_path: str):
        try:
            # For uploaded files, we need to handle the actual file content
            # For now, simulate processing with filename-based routing
            from app.core.vector_store.store_manager import store_manager
            
            # Route to appropriate store
            vector_store = store_manager.route_to_department("", file_path)
            
            # Simulate embedding creation for the filename
            embedding = self.embeddings.generate_single_embedding(file_path)
            store = store_manager.get_store(vector_store)
            
            # Store the document reference
            await store.insert_embeddings([{
                'content': f"Document: {file_path}",
                'embedding': embedding,
                'metadata': {'filename': file_path, 'type': 'document_reference'}
            }])
            
            return {
                "status": "completed",
                "vector_store": vector_store
            }
        except Exception as e:
            print(f"Document processing error: {e}")
            return {
                "status": "failed",
                "vector_store": "land_acquisition",
                "error": str(e)
            }

document_agent = DocumentProcessingAgent()