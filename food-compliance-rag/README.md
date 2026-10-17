# Food Regulatory Compliance RAG

A Retrieval-Augmented Generation (RAG) pipeline for FSSAI food regulatory compliance assessment. Ingests official regulatory PDFs, generates vector embeddings, stores them in Supabase PostgreSQL with pgvector, and provides AI-powered compliance analysis.

## Architecture

```
PDF Files → PyMuPDF Extraction → Text Chunking → OpenAI Embeddings
                                                        ↓
User Query → Embed Query → pgvector Cosine Search → Retrieved Chunks
                                                        ↓
                                    Company Evidence + Retrieved Regulations
                                                        ↓
                                    LLM Compliance Assessment → Structured JSON
```

## Tech Stack (100% Free Tier Supported)

| Component       | Free Stack (Recommended)      | OpenAI Alternative (Paid) |
|-----------------|-------------------------------|---------------------------|
| API             | FastAPI + Uvicorn             | FastAPI + Uvicorn         |
| Database        | Supabase PostgreSQL + pgvector| Supabase PostgreSQL + pgvector |
| PDF Extraction  | PyMuPDF                       | PyMuPDF                   |
| Embeddings      | **FastEmbed** (`bge-small`, 384d, local, 0 API key) | OpenAI `text-embedding-3-small` (1536d) |
| LLM / Chat      | **Groq** (`llama-3.3-70b-versatile`, 100% Free API) | OpenAI `gpt-4o-mini`      |
| DB Driver       | psycopg 3 + connection pool   | psycopg 3 + connection pool |
| Validation      | Pydantic v2                   | Pydantic v2               |
| Testing         | Pytest                        | Pytest                    |

## Setup Instructions (Windows PowerShell)

### 1. Install Dependencies

```powershell
cd "d:\Regulatory Complance\food-compliance-rag"
pip install -r requirements.txt
```

### 2. Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and create a new project.
2. Note the **project password** you set during creation.
3. Wait for the project to finish provisioning.

### 3. Run the SQL Setup Script

1. In the Supabase Dashboard, go to **SQL Editor**.
2. Click **New Query**.
3. Copy the entire contents of [`sql/001_setup.sql`](sql/001_setup.sql) and paste it.
4. Click **Run** (or press Ctrl+Enter).
5. You should see "Success. No rows returned." — this means the schema was created.

### 4. Find Your Database Connection Details

1. In Supabase Dashboard → **Settings** → **Database**.
2. Under **Connection parameters**, you will find:
   - **Host**: something like `db.xxxxxxxxxxxxxxxxxxxx.supabase.co`
   - **Port**: `5432`
   - **Database name**: `postgres`
   - **User**: `postgres`
   - **Password**: the password you set when creating the project

### 5. Configure Environment Variables

```powershell
# Copy the example and fill in your values
Copy-Item .env.example .env
notepad .env
```

Edit `.env` with your actual values:

```env
# ── Supabase (Free on supabase.com) ──
SUPABASE_DB_HOST=db.your-project-id.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-project-password
SUPABASE_DB_SSLMODE=require

# ── 100% FREE AI STACK ──
# Get your free Groq API key at https://console.groq.com
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your-free-groq-key
GROQ_CHAT_MODEL=llama-3.3-70b-versatile

# FastEmbed runs 100% locally on your CPU (0 API keys needed, 384 dimensions)
EMBEDDING_PROVIDER=fastembed
FASTEMBED_MODEL=BAAI/bge-small-en-v1.5

# ── RAG Tuning ──
CHUNK_SIZE=900
CHUNK_OVERLAP=120
RETRIEVAL_TOP_K=5
```

### 6. Test the Database Connection

```powershell
python -c "from app.database import check_connection; print(check_connection())"
```

Expected output: `{'status': 'connected', 'version': 'PostgreSQL 15...'}`

### 7. Ingest Regulatory PDFs

```powershell
python -m app.ingest
```

This will:
- Extract text from all PDFs in `data/regulations/`
- Split text into ~900-character overlapping chunks
- Generate OpenAI embeddings for each chunk
- Store everything in Supabase with deduplication
- Report progress and any errors

### 8. Test Semantic Search

```powershell
python -m app.search "What hygiene records should a food facility maintain?"
python -m app.search "labelling requirements for packaged food"
python -m app.search "food additive limits and permitted levels"
```

### 9. Start the FastAPI Server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 10. Open Swagger Documentation

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### 11. Test a Compliance Assessment

```powershell
$body = @{
    question = "What are the labelling requirements for packaged food products?"
    company_evidence = "Our facility labels all products with: product name, ingredient list, net weight, manufacturing date, expiry date, manufacturer address, and FSSAI license number."
    facility_description = "Medium-scale packaged food manufacturing unit"
    compliance_area = "Food Labelling"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/compliance/check" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### 12. Run Tests

```powershell
# Unit tests (no DB/API required)
pytest tests/ -v

# With DB integration tests (requires .env configured)
pytest tests/ -v --tb=short
```

## API Endpoints

| Method | Path                | Description                          |
|--------|---------------------|--------------------------------------|
| GET    | `/health`           | Health check + DB connectivity       |
| GET    | `/documents`        | List indexed regulatory documents    |
| POST   | `/ingest`           | Trigger PDF ingestion pipeline       |
| POST   | `/search`           | Semantic search over regulations     |
| POST   | `/compliance/check` | RAG compliance assessment            |

## Compliance Status Labels

| Status                    | Meaning |
|---------------------------|---------|
| `COMPLIANT`               | Sufficient evidence supports the requirement |
| `PARTIALLY_COMPLIANT`     | Some evidence exists, but elements are missing |
| `MISSING_EVIDENCE`        | No adequate company evidence found (≠ violation) |
| `POTENTIALLY_NON_COMPLIANT` | Evidence contradicts or violates a requirement |
| `NEEDS_REVIEW`            | Evidence is ambiguous, conflicting, or insufficient |

## Project Structure

```
food-compliance-rag/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI application
│   ├── config.py           # Settings from environment
│   ├── database.py         # psycopg3 connection pool
│   ├── schemas.py          # Pydantic request/response models
│   ├── pdf_extractor.py    # PyMuPDF text extraction
│   ├── chunker.py          # Text chunking with overlap
│   ├── embeddings.py       # OpenAI embedding generation
│   ├── vector_store.py     # Supabase pgvector persistence
│   ├── retriever.py        # Semantic retrieval service
│   ├── compliance.py       # RAG compliance assessment
│   ├── ingest.py           # Ingestion pipeline + CLI
│   └── search.py           # Search CLI
├── sql/
│   └── 001_setup.sql       # Complete Supabase schema
├── data/
│   └── regulations/        # FSSAI regulatory PDFs
├── tests/
│   └── test_pipeline.py    # Unit + integration tests
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Disclaimer

This tool is for informational purposes only. It does not constitute legal advice, official certification, or a regulatory determination. Consult qualified regulatory professionals for formal compliance decisions.
