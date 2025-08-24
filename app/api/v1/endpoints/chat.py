"""Chat endpoint for simple Q&A."""

import time
from fastapi import APIRouter
from app.models.chat import ChatRequest  # , FeedbackRequest
from app.models.query import QueryResponse
# from app.core.memory.chat_memory import chat_memory  # Commented out for now
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

async def enhance_query(query: str) -> str:
    """Enhance query with spelling correction and better search terms."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"""Fix spelling mistakes and enhance this query for legal document search:

Original: "{query}"

Rules:
1. Fix all spelling and grammar errors
2. Expand legal abbreviations (e.g., "sec" → "section")
3. Add relevant legal synonyms
4. Keep the original meaning intact
5. Make it more searchable

Return ONLY the corrected and enhanced query:"""
        response = llm.invoke(prompt)
        enhanced = response.content.strip().strip('"').strip("'")
        return enhanced if enhanced and len(enhanced) > 5 else query
    except Exception:
        return query

async def generate_format_specific_answer(query: str, context: str, response_format: str, original_query: str = "") -> tuple[str, str]:
    """Generate two different answers: precise (short) and detailed (full)."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY"))
        display_query = original_query or query
        
        # Generate PRECISE answer (always short)
        precise_prompt = f"""Answer this question with ONLY the key facts in 1-2 sentences.

Question: "{display_query}"

Context: {context[:1500]}

Rules:
- Maximum 2 sentences
- Include only essential facts/procedures
- No explanations or background
- Direct answer only

Precise Answer:"""
        
        # Generate DETAILED answer based on format
        if response_format == "structured":
            detailed_prompt = f"""Answer this question with organized bullet points.

Question: "{display_query}"

Context: {context}

Format:
• Use bullet points (•) for main points
• Use sub-bullets (  - ) for details
• Include procedures, steps, requirements
• Organize logically

Structured Answer:"""
        
        elif response_format == "descriptive":
            detailed_prompt = f"""Answer this question with detailed explanation.

Question: "{display_query}"

Context: {context}

Format:
- Comprehensive explanation with background
- Include context and implications
- 3-5 sentences with full details
- Explain significance and consequences

Detailed Answer:"""
        
        else:  # concise
            detailed_prompt = f"""Answer this question concisely but completely.

Question: "{display_query}"

Context: {context}

Format:
- Complete answer in 2-3 sentences
- Include all key information
- More detail than precise answer
- Clear and direct

Concise Answer:"""
        
        # Generate both answers
        precise_response = llm.invoke(precise_prompt)
        detailed_response = llm.invoke(detailed_prompt)
        
        precise_answer = precise_response.content.strip()
        detailed_answer = detailed_response.content.strip()
        
        return precise_answer, detailed_answer
        
    except Exception as e:
        error_msg = f"Unable to process query: {str(e)}"
        return error_msg, error_msg
from app.core.vector_store.store_manager import store_manager
from app.core.embeddings.bge3_generator import bge3_generator

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=QueryResponse)
async def chat_message(request: ChatRequest):
    """Simple chat without memory - just answer the query."""
    start_time = time.time()
    
    try:
        # Enhanced query with spelling correction
        enhanced_query = await enhance_query(request.query)
        print(f"Original: {request.query}")
        print(f"Enhanced: {enhanced_query}")
        
        # Search documents with enhanced query
        store = store_manager.get_store("documents")
        embedding = bge3_generator.generate_single_embedding(enhanced_query)
        results = await store.search(embedding, top_k=15)
        
        # Filter results by relevance
        filtered_results = [r for r in results if r.get('similarity', 0) > 0.3]
        
        # Generate answer with context
        if filtered_results:
            # Build context from top results
            context_parts = []
            for r in filtered_results[:8]:  # Use top 8 results
                metadata = r.get('metadata', {})
                doc_info = f"[Document: {metadata.get('filename', 'Unknown')}]"
                if metadata.get('line_number'):
                    doc_info += f" [Line: {metadata.get('line_number')}]"
                context_parts.append(f"{doc_info}\n{r['content']}")
            
            document_context = "\n\n".join(context_parts)
            precise_answer, detailed_answer = await generate_format_specific_answer(
                enhanced_query, document_context, request.response_format, request.query
            )
        else:
            detailed_answer = f"No relevant information found for '{request.query}'. Please try rephrasing your question or check for spelling errors."
            precise_answer = detailed_answer
        
        # message_id = 1  # Commented out session storage
        
        # Prepare sources from filtered results
        sources = []
        for result in filtered_results[:5]:  # Show top 5 relevant sources
            metadata = result.get('metadata', {})
            sources.append({
                "content": result['content'][:250] + "..." if len(result['content']) > 250 else result['content'],
                "similarity": round(result.get('similarity', 0), 3),
                "document": metadata.get('filename', 'Unknown'),
                "line_number": metadata.get('line_number', 0)
            })
        
        return QueryResponse(
            query=request.query,
            answer=detailed_answer,
            precise_answer=precise_answer,
            process_time=round(time.time() - start_time, 3),
            query_count=1,
            sources=sources,
            total_results=len(filtered_results),
            suggestions=[],
            # session_id=session_id,  # Commented out
            # message_id=message_id   # Commented out
        )
        
    except Exception as e:
        error_msg = f"Chat error: {str(e)}"
        return QueryResponse(
            query=request.query,
            answer=error_msg,
            precise_answer=error_msg,
            process_time=round(time.time() - start_time, 3),
            query_count=1,
            sources=[],
            total_results=0,
            suggestions=[],
            # session_id=session_id  # Commented out
        )

# @router.post("/feedback")
# async def submit_feedback(feedback: FeedbackRequest):
#     """Submit feedback for improvement."""
#     try:
#         await chat_memory.add_feedback(feedback)
#         return {"message": "Feedback received", "status": "success"}
#     except Exception as e:
#         return {"message": f"Feedback error: {str(e)}", "status": "error"}

# @router.get("/session/{session_id}")
# async def get_session_history(session_id: str):
#     """Get chat session history."""
#     try:
#         messages = await chat_memory.get_session_context(session_id, limit=50)
#         return {"session_id": session_id, "messages": messages}
#     except Exception as e:
#         return {"error": f"Session error: {str(e)}"}