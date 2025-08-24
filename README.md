# LangGraph Agentic RAG System

**Intelligent Document Processing & Retrieval System** with line-by-line embedding storage and comprehensive search capabilities.

## 🏗️ Architecture

- **Single Vector Store**: All documents stored in unified PostgreSQL + pgvector database
- **Line-by-Line Processing**: Every text line becomes a searchable embedding
- **Dual-LLM System**: Phi-4 (primary) + OpenAI GPT-4o (backup) with intelligent fallback
- **Complete PDF Extraction**: Full text extraction using pdfplumber + PyPDF2
- **BGE-3 Embeddings**: High-quality embeddings using BAAI/bge-large-en-v1.5
- **HNSW Vector Search**: Optimized similarity search with configurable parameters

## 📁 Project Structure

```
app/
├── api/v1/endpoints/     # FastAPI endpoints
│   ├── upload.py         # Document upload & processing
│   └── query.py          # Search & retrieval
├── core/
│   ├── document/         # Document processing
│   │   ├── pdf_extractor.py    # PDF text extraction
│   │   └── text_chunker.py     # Text processing
│   ├── embeddings/       # Embedding generation
│   │   └── bge3_generator.py   # BGE-3 model
│   ├── vector_store/     # Vector database
│   │   ├── postgresql_store.py # PostgreSQL + pgvector
│   │   └── store_manager.py    # Store management
│   └── startup.py        # Application initialization
├── agents/               # LangGraph agents
│   ├── rag_agent.py      # RAG workflow
│   └── document_agent.py # Document processing
├── config/               # Configuration
│   ├── settings.py       # Database & API settings
│   └── langgraph_config.py # LangGraph configuration
└── models/               # Data models
    ├── document.py       # Document models
    └── query.py          # Query models
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Setup PostgreSQL with pgvector
python scripts/setup_database.py
```

### 3. Environment Configuration
```bash
cp .env.example .env
```

Add your configuration:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=agentic_rag_db

# LLM APIs
AZURE_AI_ENDPOINT=your_azure_endpoint
AZURE_AI_API_KEY=your_azure_key
OPENAI_API_KEY=your_openai_key
```

### 4. Run Application

**Option 1: Direct Python**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Option 2: Docker**
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t agentic-rag .
docker run -p 8000:8000 --env-file .env agentic-rag
```

## 📡 API Usage

### Upload Documents (Line-by-Line Processing)
```bash
curl -X POST "http://localhost:8000/api/v1/upload/documents" \
  -F "files=@document.pdf" \
  -F "files=@another.pdf"
```

**Response:**
```json
[
  {
    "document_id": "doc_1",
    "filename": "document.pdf",
    "status": "completed",
    "message": "Processed 2847 lines into documents store"
  }
]
```

### Search Documents (Simple Query)
```bash
curl -X POST "http://localhost:8000/api/v1/query/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "how many objections received from farmers"}'
```

**Response:**
```json
{
  "query": "how many objections received from farmers",
  "answer": "17,000 objections were received from farmers...",
  "process_time": 3.287,
  "query_count": 1,
  "sources": [
    {
      "content": "Over 17,000 objections on 9.2 of LPS were received...",
      "similarity": 0.814,
      "document": "APCRDA LPS Book.pdf",
      "line_number": 245,
      "store": "documents"
    }
  ]
}
```

## 🔧 Key Features

### Document Processing
- **Complete PDF Extraction**: Every line of text extracted and stored
- **Batch Processing**: Handles large documents (1000+ pages)
- **Progress Tracking**: Real-time processing status
- **Error Handling**: Robust PDF extraction with fallback methods

### Intelligent Search
- **Line-Level Precision**: Search finds exact text lines
- **Similarity Scoring**: Ranked results with confidence scores
- **Multi-Document Search**: Searches across all uploaded documents
- **Source Attribution**: Shows exact document and line number

### LLM Integration
- **Primary**: Phi-4 via Azure AI Services
- **Backup**: OpenAI GPT-4o/GPT-4o-mini
- **Automatic Fallback**: Seamless switching on API failures
- **Context-Aware**: Uses retrieved document content for answers

## 🗄️ Database Schema

**Single Vector Store Table:**
```sql
CREATE TABLE embeddings_documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB DEFAULT '{}'
);

-- HNSW Index for fast similarity search
CREATE INDEX hnsw_idx_documents 
ON embeddings_documents 
USING hnsw (embedding vector_ip_ops);
```

**Metadata Structure:**
```json
{
  "filename": "document.pdf",
  "line_number": 123,
  "type": "document_line",
  "document_type": "pdf"
}
```

## ⚡ Performance

**Processing Speed:**
- **150-page document**: ~8-15 minutes
- **Lines per minute**: ~200-300 lines
- **Batch size**: 20 lines per database insert
- **Memory usage**: Optimized for large documents

**Search Performance:**
- **Query time**: 2-5 seconds
- **Results**: Top 50 most similar lines
- **HNSW parameters**: m=16, ef_construction=200, ef_search=100

## 🔒 Security

- **Environment Variables**: All secrets in .env file
- **CORS Configuration**: Restricted to localhost:5173
- **Input Validation**: File type and size restrictions
- **Error Handling**: No sensitive data in error messages

## 🛠️ Development

### Testing
```bash
# Check database content
python check_database_content.py

# Clear and add sample content
python clear_and_test.py
```

### Configuration
- **Vector Store**: Single "documents" store for all content
- **Embedding Model**: BGE-3 (1024 dimensions)
- **Chunk Size**: Line-by-line (no chunking)
- **Similarity Threshold**: 0.3 minimum for results

## 📋 Requirements

- **Python**: 3.12+
- **PostgreSQL**: 14+ with pgvector extension
- **Memory**: 4GB+ RAM recommended
- **Storage**: Depends on document volume
- **GPU**: Optional (for faster embeddings)

## 🔄 Workflow

1. **Upload**: PDF → Text Extraction → Line Splitting
2. **Embed**: Each Line → BGE-3 → 1024D Vector
3. **Store**: Vector + Metadata → PostgreSQL + HNSW Index
4. **Search**: Query → Embedding → Similarity Search → LLM Answer
5. **Response**: Answer + Sources + Metadata