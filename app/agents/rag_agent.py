"""LangGraph RAG Agent."""

import os
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from app.core.embeddings.bge3_generator import bge3_generator
from pydantic import BaseModel

class RAGState(BaseModel):
    query: str
    confidence: float = 0.0
    response: str = ""
    llm_used: str = ""

class AgenticRAGSystem:
    def __init__(self):
        self.phi4_llm = None
        self.backup_llm = None
        self.graph = self._build_graph()
    
    def _get_llm(self, use_smart=False):
        """Get LLM with Phi-4 primary, OpenAI backup."""
        try:
            if self.phi4_llm is None:
                from langchain_openai import AzureChatOpenAI
                self.phi4_llm = AzureChatOpenAI(
                    model="phi-4",
                    temperature=0.1 if not use_smart else 0.2,
                    azure_endpoint=os.getenv("AZURE_AI_ENDPOINT"),
                    api_key=os.getenv("AZURE_AI_API_KEY"),
                    api_version=os.getenv("AZURE_AI_API_VERSION")
                )
            return self.phi4_llm
        except Exception:
            if self.backup_llm is None:
                model = "gpt-4o" if use_smart else "gpt-4o-mini"
                self.backup_llm = ChatOpenAI(
                    model=model, 
                    temperature=0.1 if not use_smart else 0.2,
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            return self.backup_llm
    
    def _build_graph(self):
        workflow = StateGraph(RAGState)
        
        workflow.add_node("analyze", self._analyze_query)
        workflow.add_node("generate", self._generate_response)
        
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _analyze_query(self, state: RAGState):
        state.confidence = 0.8 if len(state.query.split()) < 10 else 0.6
        return state
    
    def _generate_response(self, state: RAGState):
        use_smart = state.confidence < 0.75
        llm = self._get_llm(use_smart=use_smart)
        state.llm_used = "phi-4" if hasattr(llm, 'azure_endpoint') else ("gpt-4o" if use_smart else "gpt-4o-mini")
        
        response = llm.invoke(f"Answer: {state.query}")
        state.response = response.content
        return state
    
    async def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using context from vector search."""
        try:
            llm = self._get_llm(use_smart=len(query.split()) > 10)
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nProvide a clear, concise answer based on the context:"
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Unable to generate answer: {str(e)}"
    
    async def process_query(self, query: str):
        result = await self.graph.ainvoke(RAGState(query=query))
        return {
            "response": result.response,
            "confidence": result.confidence,
            "llm_used": result.llm_used
        }

rag_agent = AgenticRAGSystem()