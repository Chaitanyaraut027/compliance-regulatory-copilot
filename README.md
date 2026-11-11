# Food Regulatory Intelligence Co-Pilot 🥗⚖️

> **A Production-Grade, Zero-Hallucination Retrieval-Augmented Generation (RAG) System for FSSAI Food Compliance Verification with Exact Page Citations.**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F05A28?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## 📌 Executive Summary

Food manufacturers, packaging designers, and quality assurance teams operate under rigorous, constantly evolving regulatory frameworks established by the **Food Safety and Standards Authority of India (FSSAI)**. Official regulatory compendiums span thousands of dense legal pages across labelling standards, food additive limits, contaminant thresholds, and hygiene licensing.

### The Problem
* **Manual Audits Are Cripplingly Slow:** Reviewing a single packaging label or plant formulation against multiple compendiums takes compliance officers days of cross-referencing.
* **Vanilla LLMs Fail in Legal Audits:** General-purpose AI models consistently hallucinate regulatory clauses, invent non-existent numerical limits, blur amendment dates, and make unsubstantiated legal claims.

### The Solution
The **Food Regulatory Intelligence Co-Pilot** combines dense vector retrieval (`pgvector`), sliding-window document chunking, and strict grounded prompting to evaluate company packaging and facility evidence against official FSSAI law in **sub-second response times**—guaranteeing **100% verifiable source citations** and **zero hallucinations**.

---

## 🏛️ System Architecture

The architecture is divided into two decoupled pipelines: an **Offline Ingestion & Vector Indexing Pipeline** and an **Online Real-Time Compliance Audit Pipeline**.

<p align="center">
  <img src="docs/images/architecture.png" alt="System Architecture Diagram" width="100%" />
</p>

### Pipeline 1: Offline Ingestion & Vector Indexing
1. **Document Ingestion:** Official FSSAI PDF compendiums (*Labelling & Display*, *Food Additives*, *Contaminants*, *Licensing*) are ingested and parsed using **PyMuPDF**.
2. **Context-Preserving Sliding Window:** Text is segmented into **~900-character chunks with a 120-character overlap**, ensuring legal clauses and threshold tables are never sliced abruptly across chunk boundaries.
3. **Metadata Attachment:** Every chunk is tagged with `page_start`, `page_end`, `section_title`, and a deterministic `content_hash`.
4. **Local Dense Vector Generation:** Chunks are vectorized using **FastEmbed (`BAAI/bge-small-en-v1.5`)**, producing 384-dimensional dense embeddings locally on CPU (with 0 external API overhead or rate limits).
5. **pgvector Storage:** Embeddings and metadata are indexed in **Supabase PostgreSQL** using an **IVFFlat cosine distance index (`vector_cosine_ops`)**.

### Pipeline 2: Real-Time Grounded Audit Engine
1. **User Submission:** The user submits company packaging text, ingredient lists, or facility practices via the **React 19 UI**.
2. **API Gateway:** The **Node.js/Express API Gateway** authenticates the user (JWT), validates inputs, logs the audit request, and proxies the query to the Python AI engine.
3. **Semantic Cosine Search:** The **FastAPI RAG Core** embeds the inquiry and executes a high-speed cosine distance search (`<=>`) in PostgreSQL, retrieving the top $K$ relevant regulatory clauses.
4. **Grounded Synthesis Guardrails:** The retrieved regulatory clauses and company evidence are assembled into a strict system prompt. The LLM (**Groq Llama-3.3-70B**) is constrained to base assessments **solely** on retrieved text.
5. **Structured Audit Output:** The engine outputs a validated **Pydantic JSON response** complete with compliance statuses, found evidence, missing proof, actionable next steps, and page-level legal citations.

---

## 🗄️ Database & Vector Schema

The system runs on **Supabase PostgreSQL 15+** with the native **`pgvector`** extension, unifying relational business entities with high-dimensional vector embeddings in a single database.

<p align="center">
  <img src="docs/images/database_er_diagram.png" alt="Database Entity Relationship Diagram" width="100%" />
</p>

### Relational Entity Details

| Table | Purpose | Key Attributes | Indexes & Constraints |
|:---|:---|:---|:---|
| **`users`** | User management & Role-Based Access Control | `id (UUID)`, `name`, `email`, `password_hash`, `role` (`user`/`admin`) | `PRIMARY KEY (id)`, `UNIQUE (email)` |
| **`documents`** | Ingested official FSSAI regulatory compendiums | `id (UUID)`, `filename`, `title`, `page_count`, `file_hash`, `metadata` | `PRIMARY KEY (id)`, `UNIQUE (filename)` |
| **`document_chunks`** | Semantic text chunks + 384d vector embeddings | `id (UUID)`, `document_id (FK)`, `content`, `embedding (vector(384))`, `page_start`, `page_end`, `section_title`, `content_hash` | `FK (document_id) REFERENCES documents(id) ON DELETE CASCADE`<br/>`UNIQUE (document_id, content_hash)`<br/>`IVFFlat (embedding vector_cosine_ops)` |
| **`audit_history`** | Persistent audit records for compliance verification | `id (UUID)`, `user_id (FK)`, `question`, `compliance_area`, `company_evidence`, `overall_status`, `findings (JSONB)`, `summary` | `FK (user_id) REFERENCES users(id) ON DELETE CASCADE`<br/>`INDEX (user_id)`, `INDEX (created_at DESC)` |
| **`company_policy_docs`**| User-uploaded internal SOPs & specification PDFs | `id (UUID)`, `user_id (FK)`, `filename`, `extracted_text`, `char_count` | `FK (user_id) REFERENCES users(id) ON DELETE CASCADE` |

### Stored Procedure for Cosine Distance Search
```sql
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding     vector(384),
    match_count         INTEGER DEFAULT 5,
    filter_document_id  UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID, document_id UUID, content TEXT, page_start INTEGER,
    page_end INTEGER, section_title TEXT, similarity FLOAT,
    doc_filename TEXT, doc_title TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id, dc.document_id, dc.content, dc.page_start, dc.page_end,
        dc.section_title,
        1 - (dc.embedding <=> query_embedding) AS similarity,
        d.filename AS doc_filename, d.title AS doc_title
    FROM document_chunks dc
    JOIN documents d ON d.id = dc.document_id
    WHERE (filter_document_id IS NULL OR dc.document_id = filter_document_id)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

## 💻 User Interface & Live Dashboard

The application provides a responsive, high-contrast dashboard built with **React 19**, **Vite**, and **Tailwind CSS**.

<p align="center">
  <img src="docs/images/dashboard_preview.png" alt="Food Compliance Portal Dashboard Preview" width="100%" />
</p>

### Key Frontend Features
* **Automated Audit Inquiry Form:** Input facility practices, ingredient ratios, or packaging copy with instant AI assessment.
* **Document Upload & Parsing:** Drag-and-drop proprietary packaging artwork or facility SOP PDFs with automated server-side text extraction.
* **Semantic Regulations Explorer:** Search across thousands of official FSSAI clauses using natural language questions without needing exact keyword matching.
* **Audit History & Reporting:** Track historical compliance audits, export structured reports, and review historical compliance trends over time.

---

## 🛡️ Hallucination Guardrails & Status Matrix

To prevent unsafe legal assumptions, the RAG engine enforces a strict 5-tier status evaluation matrix:

| Status Badge | Formal Definition | System Decision Logic |
|:---|:---|:---|
| <kbd>**COMPLIANT**</kbd> | Requirements fully satisfied | Provided evidence explicitly fulfills all retrieved regulatory conditions. |
| <kbd>**PARTIALLY_COMPLIANT**</kbd> | Missing declaration elements | Core requirement is met, but mandatory sub-elements (e.g. font size, allergen icon) are absent. |
| <kbd>**MISSING_EVIDENCE**</kbd> | Insufficient documentation | No adequate company evidence was provided. **Does not equate to a legal violation.** |
| <kbd>**POTENTIALLY_NON_COMPLIANT**</kbd> | Potential regulatory breach | Submitted evidence directly contradicts a defined clause, limit, or threshold. |
| <kbd>**NEEDS_REVIEW**</kbd> | Ambiguous or outdated evidence | Evidence is conflicting or requires manual inspection by a certified regulatory officer. |

---

## ⚡ Tech Stack & Architecture Choices

| Component | Technology | Rationale |
|:---|:---|:---|
| **Frontend** | React 19 + TypeScript + Tailwind CSS | Ultra-fast Vite build, responsive layout, type-safe API communication. |
| **API Gateway** | Node.js + Express + Multer + JWT | Centralized authentication, bcrypt password hashing, file upload stream processing. |
| **AI / RAG Microservice** | FastAPI + Uvicorn + Pydantic v2 | High-concurrency Python runtime, async vector query execution, strict schema enforcement. |
| **Database & Vector Store** | PostgreSQL 15 + `pgvector` (Supabase) | Single ACID-compliant database combining relational users/audits with vector indexing. |
| **Embedding Model** | FastEmbed (`bge-small-en-v1.5`) | 384-dimensional dense vectors running locally on CPU with **zero API cost**. |
| **Inference LLM** | Groq (`llama-3.3-70b-versatile`) | Ultra-fast token generation (~250 tokens/sec), strict JSON mode adherence. |
| **PDF Extraction** | PyMuPDF (`fitz`) | High-speed text extraction retaining exact page coordinates and structural layout. |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python 3.11+**
- **Node.js v18+** & **npm**
- A **Supabase** account (Free tier supported)
- A **Groq Cloud** API Key (Free tier at [console.groq.com](https://console.groq.com))

---

### 2. Database Setup
1. Create a new project in the [Supabase Dashboard](https://supabase.com).
2. Open the **SQL Editor** in Supabase and execute:
   - [`food-compliance-rag/sql/001_setup.sql`](food-compliance-rag/sql/001_setup.sql) *(Enables pgvector, creates documents, document_chunks, and search procedure)*
   - [`food-compliance-rag/sql/002_node_backend.sql`](food-compliance-rag/sql/002_node_backend.sql) *(Creates users, audit_history, and company_policy_docs)*

---

### 3. Environment Configuration
Create `.env` inside `food-compliance-rag/`:
```env
# Supabase PostgreSQL
SUPABASE_DB_HOST=db.your-project.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-secure-password
SUPABASE_DB_SSLMODE=require

# Groq Free AI Stack
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your-free-groq-key
GROQ_CHAT_MODEL=llama-3.3-70b-versatile

# FastEmbed (Local CPU, 384 dimensions)
EMBEDDING_PROVIDER=fastembed
FASTEMBED_MODEL=BAAI/bge-small-en-v1.5

# RAG Hyperparameters
CHUNK_SIZE=900
CHUNK_OVERLAP=120
RETRIEVAL_TOP_K=5
```

Create `.env` inside `node-backend/`:
```env
PORT=3000
FASTAPI_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
JWT_SECRET=super_secret_jwt_key_change_in_production
JWT_EXPIRES_IN=7d
MAX_FILE_SIZE_MB=5
UPLOAD_DIR=uploads/
```

---

### 4. Ingest Regulatory Compendiums
Run the automated ingestion pipeline to parse, chunk, embed, and index all FSSAI PDFs into pgvector:
```powershell
cd "d:\Regulatory Complance\food-compliance-rag"
.\.venv\Scripts\Activate.ps1
python -m app.ingest
```

---

### 5. Start All Services

You can launch all 3 services concurrently using the provided one-click scripts:

#### Windows PowerShell:
```powershell
.\run_react.ps1
```

#### Windows Batch:
```cmd
run_react.bat
```

#### Or start manually in separate terminals:
```bash
# Terminal 1: FastAPI RAG Engine (Port 8000)
cd food-compliance-rag
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Node.js API Gateway (Port 3000)
cd node-backend
npm run dev

# Terminal 3: React Frontend (Port 5173)
cd frontend
npm run dev
```

Once running:
- **React Web Application:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Node.js Gateway Health Check:** [http://localhost:3000/](http://localhost:3000/)

---

## 📡 API Reference

### FastAPI AI Engine (`http://localhost:8000`)

#### `POST /compliance/check`
Executes an end-to-end grounded RAG compliance evaluation.
```json
// Request Body
{
  "question": "What are mandatory labelling requirements for packaged foods?",
  "company_evidence": "Product: NutriOats. Ingredients: Oats, honey. Net Wt: 500g. Mfg Date: Oct 2026. Lic No: 10018021003456.",
  "facility_description": "Packaged snack manufacturing facility",
  "compliance_area": "Food Labelling"
}

// Response Body (Truncated)
{
  "overall_status": "PARTIALLY_COMPLIANT",
  "summary": "Product complies with basic labelling but lacks a mandatory nutritional facts panel and veg/non-veg logo.",
  "findings": [
    {
      "requirement": "Declaration of Nutritional Information per 100g",
      "status": "MISSING_EVIDENCE",
      "evidence_found": [],
      "evidence_missing": ["Nutritional information per 100g or per serve"],
      "recommended_actions": ["Add nutritional panel showing energy (kcal), protein, carbohydrate, and fat values."]
    }
  ],
  "sources": [
    {
      "document_name": "Compendium_Labelling_Display_17_10_2022.pdf",
      "page_start": 12,
      "page_end": 14,
      "similarity": 0.892
    }
  ]
}
```

---

## 🧪 Testing & Verification

The test suite covers both unit logic (mocked embeddings, schema validation) and integration with the live vector database.

```powershell
# Run Python FastAPI tests
cd food-compliance-rag
pytest tests/ -v

# Run Node.js API Gateway test suite
cd ..\node-backend
npm test
```

---

## 📄 License
This project is open-source and licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for full details.

