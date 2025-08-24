"""LangGraph RAG workflow with agentic decision making."""

from typing import Dict, Any, List, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from app.core.embeddings.bge3_generator import bge3_generator
from pydantic import BaseModel

class RAGWorkflowState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str = ""
    confidence: float = 0.0
    vector_stores: List[str] = []
    retrieved_context: str = ""
    final_response: str = ""
    llm_choice: str = ""

def create_rag_workflow():
    """Create the main RAG workflow using LangGraph."""
    
    # Initialize LLMs and embeddings
    fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    smart_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    embeddings = bge3_generator
    
    def analyze_query(state: RAGWorkflowState) -> RAGWorkflowState:
        """Analyze query complexity and determine confidence."""
        query = state.query or state.messages[-1].content
        
        # Simple heuristic for confidence
        word_count = len(query.split())
        has_complex_terms = any(term in query.lower() for term in ["compare", "analyze", "explain why", "how does"])
        
        state.confidence = 0.9 if word_count < 10 and not has_complex_terms else 0.6
        state.query = query
        
        return state
    
    def route_vector_stores(state: RAGWorkflowState) -> RAGWorkflowState:
        """Route to appropriate vector stores based on content."""
        query_lower = state.query.lower()
        
        stores = []
        if any(term in query_lower for term in ["technical", "code", "api", "system"]):
            stores.append("tech")
        if any(term in query_lower for term in ["business", "strategy", "market"]):
            stores.append("business")
        if any(term in query_lower for term in ["legal", "compliance", "regulation"]):
            stores.append("legal")
        
        state.vector_stores = stores if stores else ["general"]
        return state
    
    def retrieve_documents(state: RAGWorkflowState) -> RAGWorkflowState:
        """Retrieve relevant documents using HNSW search."""
        # Generate embedding for query
        query_embedding = embeddings.generate_single_embedding(state.query)
        
        # Simulate HNSW retrieval from multiple stores
        retrieved_docs = []
        for store in state.vector_stores:
            # In real implementation, this would query PostgreSQL with HNSW
            retrieved_docs.append(f"Document from {store} store relevant to: {state.query}")
        
        state.retrieved_context = "\n".join(retrieved_docs)
        return state
    
    def choose_llm(state: RAGWorkflowState) -> str:
        """Decide which LLM to use based on confidence."""
        return "use_fast_llm" if state.confidence >= 0.75 else "use_smart_llm"
    
    def generate_with_fast_llm(state: RAGWorkflowState) -> RAGWorkflowState:
        """Generate response using GPT-4o-mini for simple queries."""
        prompt = f"Context: {state.retrieved_context}\n\nQuery: {state.query}\n\nProvide a concise answer:"
        
        response = fast_llm.invoke([HumanMessage(content=prompt)])
        state.final_response = response.content
        state.llm_choice = "gpt-4o-mini"
        
        return state
    
    def generate_with_smart_llm(state: RAGWorkflowState) -> RAGWorkflowState:
        """Generate response using GPT-4o for complex queries."""
        prompt = f"Context: {state.retrieved_context}\n\nQuery: {state.query}\n\nProvide a detailed, well-reasoned answer:"
        
        response = smart_llm.invoke([HumanMessage(content=prompt)])
        state.final_response = response.content
        state.llm_choice = "gpt-4o"
        
        return state
    
    # Build the workflow graph
    workflow = StateGraph(RAGWorkflowState)
    
    # Add nodes
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("route_stores", route_vector_stores)
    workflow.add_node("retrieve_docs", retrieve_documents)
    workflow.add_node("generate_fast_llm", generate_with_fast_llm)
    workflow.add_node("generate_smart_llm", generate_with_smart_llm)
    
    # Add edges
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "route_stores")
    workflow.add_edge("route_stores", "retrieve_docs")
    
    # Conditional routing based on confidence
    workflow.add_conditional_edges(
        "retrieve_docs",
        choose_llm,
        {
            "use_fast_llm": "generate_fast_llm",
            "use_smart_llm": "generate_smart_llm"
        }
    )
    
    workflow.add_edge("generate_fast_llm", END)
    workflow.add_edge("generate_smart_llm", END)
    
    return workflow.compile()

# Global workflow instance
rag_workflow = create_rag_workflow()