# DocMind AI — Document Intelligence & RAG Workspace

DocMind AI is a document-focused RAG and agent system for uploading documents, searching their contents, and asking questions using natural language.

It combines a FastAPI backend, PostgreSQL persistence, hybrid retrieval using dense FAISS and BM25 search, Reciprocal Rank Fusion (RRF), cross-encoder reranking, citation validation, and token-aware conversation memory.

## Key Features

- **Multi-Document Ingestion** — Upload PDF, DOCX, TXT, and Markdown files with automatic text extraction, chunking, and metadata handling.
- **Hybrid Retrieval** — Combines dense FAISS retrieval with BM25 lexical search using Reciprocal Rank Fusion (RRF).
- **Cross-Encoder Reranking** — Re-ranks retrieved document chunks to improve relevance before generating an answer.
- **Document-Grounded Answers** — Answers are generated using retrieved document context with supporting source citations.
- **Agent-Based Document Search** — Routes document-related requests through a controlled agent and document search pipeline.
- **Conversation Memory** — Maintains conversation context with token-aware memory and summarization.
- **Multi-Provider LLM Support** — Supports Groq, OpenAI, and Ollama through the LLM manager.
- **Encrypted Credentials** — LLM API credentials stored in PostgreSQL are encrypted at rest using Fernet encryption.
- **Persistent Chat History** — Conversations and messages are stored in PostgreSQL and remain available after browser or server restarts.
- **Document Scoping** — Chat queries can be restricted to selected documents.
- **Document Insights** — Provides an overview of the documents and indexed content in the knowledge base.

## System Architecture

                    +-----------------------------+
                    |       DocMind AI Web UI     |
                    |       HTML / CSS / JS       |
                    +-------------+---------------+
                                  |
                                  | REST API
                                  v
                    +-----------------------------+
                    |      FastAPI Backend        |
                    +-------------+---------------+
                                  |
             +--------------------+--------------------+
             |                    |                    |
             v                    v                    v
     +---------------+    +---------------+    +---------------+
     |  PostgreSQL   |    | Agent Layer   |    | Retrieval     |
     |  Persistence  |    |               |    | Pipeline      |
     +---------------+    +---------------+    +---------------+
     | Users         |    | Router        |    | FAISS         |
     | Documents     |    | Orchestrator  |    | BM25          |
     | Conversations |    | Tools         |    | RRF           |
     | Messages      |    | Memory        |    | Reranker      |
     | Settings      |    +---------------+    +---------------+
     +---------------+             |                    |
             |                     +---------+----------+
             |                               |
             +-------------------------------v
                                  +-------------------+
                                  |   LLM Providers   |
                                  | Groq / OpenAI /   |
                                  | Ollama            |
                                  +-------------------+

## Retrieval Pipeline

For document questions, DocMind AI uses a hybrid retrieval pipeline:

User Query
    |
    +----------------------+
    |                      |
    v                      v
FAISS Dense Search     BM25 Search
    |                      |
    +----------+-----------+
               |
               v
       Reciprocal Rank
          Fusion
             |
             v
      Cross-Encoder
        Reranking
             |
             v
    Citation Validation
             |
             v
       LLM Response

## Tech Stack

### Backend
- Python
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy

### Database
- PostgreSQL
- Psycopg
- Alembic

### Retrieval & RAG
- FAISS
- Sentence Transformers
- BM25
- Reciprocal Rank Fusion
- Cross-Encoder Reranking

### Document Processing
- PyMuPDF
- python-docx
- Markdown/text processing

### LLM Integration
- Groq
- OpenAI
- Ollama
- LangChain integrations

### Security
- Python Cryptography
- Fernet encryption for stored LLM credentials

### Frontend
- HTML
- CSS
- Vanilla JavaScript

### Testing
- Pytest
- FastAPI TestClient

## Project Structure

DocMind-AI/
|
├── agent/                    # Agent routing, orchestration, and tools
│   └── tools/                # Document search and metadata tools
|
├── backend/                  # FastAPI application
│   ├── api/                  # API routes
│   ├── core/                 # Configuration, logging, security
│   ├── database/             # SQLAlchemy models and database configuration
│   ├── schemas/              # Request and response schemas
│   └── services/             # Application services
|
├── memory/                   # Conversation context and token management
├── repositories/             # PostgreSQL data access layer
├── retrieval/                # FAISS, BM25, RRF, and reranking
├── evaluation/               # Retrieval, citation, and answer evaluation
├── scripts/                  # Maintenance and migration utilities
├── static/                   # CSS and JavaScript
├── templates/                # Web interface templates
├── tests/                    # Automated test suite
├── documents/                # Runtime document storage
├── vectors/                  # Runtime vector indexes
├── alembic/                  # Database migrations
|
├── chat_manager.py           # Chat management facade
├── database.py               # Database facade
├── document_processor.py     # Document processing
├── embeddings.py             # Embedding utilities
├── llm_manager.py            # LLM provider management
├── rag_pipeline.py           # RAG pipeline
├── vector_store.py           # Vector store management
|
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md

## Configuration

DocMind AI uses PostgreSQL for persistence and supports external or local LLM providers.

Configuration values are provided through environment variables. See `.env.example` for the available settings.

LLM API credentials can also be configured through the application's Settings interface.

Sensitive credentials are not included in the repository.

## Database

DocMind AI uses PostgreSQL for persistent application data, including:

- Users
- Documents
- Conversations
- Messages
- Settings

Database schema management is handled through SQLAlchemy and Alembic.

## Security

LLM API credentials stored by the application are encrypted at rest using Fernet symmetric encryption.

The application also:

- Keeps `.env` files out of version control.
- Masks API credentials in API responses.
- Avoids writing API keys to application logs.
- Keeps runtime documents and vector indexes outside Git tracking.

## Testing

The project includes automated tests covering:

- API routes
- Document processing
- Retrieval
- BM25 search
- Dense retrieval
- RRF fusion
- Cross-encoder reranking
- Citation validation
- Conversation persistence
- Memory handling
- Credential encryption
- LLM configuration
- Frontend workflows

Current local verification:

92 tests passed

## Current Status

DocMind AI is currently developed as a local web application using FastAPI, PostgreSQL, and configurable LLM providers.

The repository contains the application source code, tests, database migrations, configuration templates, and deployment configuration.

Runtime data such as uploaded documents, vector indexes, logs, local databases, and environment files are intentionally excluded from version control.