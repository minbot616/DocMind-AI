# DocMind AI — Document Intelligence & RAG Workspace

DocMind AI is an end-to-end, production-grade **Retrieval-Augmented Generation (RAG) & Agent System**. It pairs a high-performance **FastAPI backend**, **PostgreSQL** database persistence, **Hybrid Retrieval (Dense FAISS + Sparse BM25)**, **Cross-Encoder Reranking**, **Strict Citation Grounding**, and **Token-Aware Context Memory** with a modern dark-mode single-page Web Workspace (HTML/CSS/JavaScript).

---

## Key Features

- **Multi-Document Ingestion**: Upload PDFs, DOCX, TXT, and Markdown files. Automatic text extraction, structural chunking, and metadata parsing.
- **Hybrid Retrieval System**: Combines **FAISS** vector embeddings (`all-MiniLM-L6-v2`) with **Sparse BM25** keyword search using **Reciprocal Rank Fusion (RRF)**.
- **Cross-Encoder Reranking**: Re-scores candidate context chunks using `cross-encoder/ms-marco-MiniLM-L-6-v2` for precise relevancy ranking.
- **Controlled Agent Orchestrator**: Multi-tool agent pipeline with intent routing, deterministic calculation tool, document search, and metadata querying.
- **Strict Citation Grounding**: Verifies generated answers against retrieved context snippets to ensure accuracy and prevent hallucinations.
- **Token-Aware Context Memory**: Tracks token budgets, automatically generates sliding conversation summaries, and manages short/long-term context.
- **Multi-Provider LLM Integration**: Out-of-the-box support for **Groq Cloud API**, **OpenAI GPT**, and local **Ollama** servers with automatic active model resolution (`llama-3.1-8b-instant`).
- **Encrypted Credentials at Rest**: Server-side Fernet encryption (`cryptography.fernet.Fernet`) for all stored LLM API keys in PostgreSQL.
- **Full History & Persistence**: Persistent PostgreSQL database tracking user sessions, uploaded documents, conversation history, and user settings.

---

## System Architecture

```text
               +----------------------------------+
               |  DocMind AI Web Interface (SPA)  |
               +----------------------------------+
                                |
                                v (REST API / JSON)
               +----------------------------------+
               |         FastAPI Backend          |
               +----------------------------------+
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
+---------------+     +--------------------+   +-------------------+
| PostgreSQL DB |     | Controlled Agent   |   | Hybrid Retrieval  |
| Persistence   |     | Orchestrator       |   | Pipeline          |
+---------------+     +--------------------+   +-------------------+
  - Users               - Intent Router          - FAISS Vector Store
  - Documents           - Tool Registry          - Sparse BM25
  - Conversations       - Token Context Manager  - Reciprocal Rank
  - Messages            - Citation Validator       Fusion (RRF)
  - Settings (Encrypted)|                        - Cross-Encoder
                        +--------------------+     Reranker
                                |              +-------------------+
                                v
                      +--------------------+
                      | LLM Provider Client|
                      | (Groq/OpenAI/Ollama|
                      +--------------------+
```

---

## Tech Stack

- **Backend**: Python 3.13, FastAPI, Uvicorn, Pydantic
- **Database & Storage**: PostgreSQL (psycopg3), SQLAlchemy 2.0, Alembic
- **Vector & RAG Retrieval**: FAISS (`faiss-cpu`), PyMuPDF (`fitz`), `python-docx`, SentenceTransformers, Rank-BM25
- **LLM Integrations**: LangChain (`langchain-groq`, `langchain-openai`, `langchain-ollama`), Groq API
- **Security**: Cryptography (`Fernet` key encryption at rest)
- **Testing**: Pytest, FastAPI TestClient

---

## Directory Structure

```text
DocMind-AI/
├── agent/                             # Autonomous Agent framework & tool implementations
│   ├── orchestrator.py                # Agent Execution Orchestrator
│   ├── router.py                      # Intent Routing engine
│   └── tools/                         # Search, Metadata, & Calculator tools
├── backend/                           # FastAPI Application Core
│   ├── api/routes/                    # REST Endpoint handlers (chat, docs, history, settings)
│   ├── core/                          # Logging, app configuration, & Fernet encryption
│   ├── database/                      # SQLAlchemy Engine, Session, & ORM Models
│   ├── schemas/                       # Pydantic Request/Response DTOs
│   └── services/                      # Business logic services
├── memory/                            # Token-budgeted context memory & summary manager
├── repositories/                      # PostgreSQL Repository Access Layer
├── retrieval/                         # Hybrid Retrieval (FAISS + BM25 + RRF + Cross-Encoder)
├── static/                            # Frontend Assets (Vanilla CSS design system & JavaScript SPA controller)
├── templates/                         # Single Page Application HTML templates
├── tests/                             # Automated Test Suite (92 tests)
└── requirements.txt                   # Python Dependencies
```

---

## Prerequisites & Installation

### 1. Prerequisites

- **Python**: 3.11+ (Python 3.13 recommended)
- **PostgreSQL**: Local instance or remote PostgreSQL server running on port `5432`

### 2. Clone & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/DocMind-AI.git
cd DocMind-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Environment Variables Configuration

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Configure your environment parameters:

```ini
# Database Configuration
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/docmind_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=docmind_db
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Application Settings
LLM_PROVIDER=Groq
LLM_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional Server-Side Secret Key for API Key Encryption at Rest
DOCMIND_SECRET_KEY=your_generated_fernet_secret_key_here
```

---

## PostgreSQL Database Initialization

1. Create local PostgreSQL database `docmind_db`:
   ```sql
   CREATE DATABASE docmind_db;
   ```
2. On initial startup, DocMind AI automatically creates all ORM database tables (`users`, `documents`, `conversations`, `messages`, `settings`) and runs schema migrations.

---

## Running the Application

Start the FastAPI backend and web server:

```bash
python -m backend.main
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000
```

---

## Running Automated Tests

Run the complete automated regression test suite:

```bash
python -m pytest tests/
```

Expected baseline output:
```text
================= 92 passed, 28 warnings in 71.57s (0:01:11) ==================
```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
