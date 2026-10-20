# Food Regulatory Compliance Copilot — Node.js API Gateway

Node.js / Express API gateway layer sitting in front of the Python FastAPI RAG service. It handles user authentication (JWT), input validation, company policy PDF text extraction, and persistent audit logging in Supabase PostgreSQL while proxying AI compliance queries to FastAPI.

---

## Architecture

```
User / Frontend (Port 8501)
         │
         ▼
Node.js Gateway (Port 3000)  ← JWT Auth, Validation, Audit Logging, PDF Parsing
         │  (proxy)
         ▼
FastAPI RAG Service (Port 8000)  ← Embeddings, pgvector semantic search, Groq LLM
         │
         ▼
Supabase PostgreSQL (Port 5432)  ← Shared DB (users, audit_history, policy_docs, documents, chunks)
```

---

## Prerequisites & Installation

- Node.js v18+ (tested on v20/v24)
- Running Supabase PostgreSQL instance
- Running FastAPI service on `http://localhost:8000`

```bash
cd node-backend
npm install
```

Copy `.env.example` to `.env` and fill in your database credentials:
```bash
cp .env.example .env
```

---

## Running the Server

```bash
# Development (with nodemon auto-reload)
npm run dev

# Production
npm start

# Automated API Test Suite
npm test
```

---

## Database Migration

The schema for this backend is defined in:
`../food-compliance-rag/sql/002_node_backend.sql`

It creates 3 tables in Supabase:
- `users`: User accounts with bcrypt hashed passwords and role (`user` or `admin`).
- `audit_history`: Audit records created automatically when compliance checks run.
- `company_policy_docs`: Extracted text from uploaded policy PDFs.

---

## API Endpoints

### 1. Authentication (`/api/auth`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user `{ name, email, password }` | No |
| `POST` | `/api/auth/login` | Login and receive JWT `{ email, password }` | No |
| `GET` | `/api/auth/me` | Fetch current authenticated user profile | Bearer Token |

### 2. Compliance AI Proxy (`/api/compliance`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/compliance/health` | Check FastAPI service health & DB status | No |
| `GET` | `/api/compliance/documents`| List available FSSAI regulatory documents | Bearer Token |
| `POST` | `/api/compliance/search` | Semantic search over regulations `{ query, top_k }` | Bearer Token |
| `POST` | `/api/compliance/check` | Assess compliance & **auto-save audit log** | Bearer Token |
| `POST` | `/api/compliance/ingest` | Trigger regulatory PDF ingestion | Bearer Token (`admin` only) |

### 3. Company Policy Upload (`/api/upload`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/upload/policy` | Multipart upload PDF (`file`), extracts text | Bearer Token |
| `GET` | `/api/upload/policies` | List all policy docs uploaded by user | Bearer Token |
| `GET` | `/api/upload/policies/:id`| Retrieve full extracted text by document ID | Bearer Token |

### 4. Audit History (`/api/audit`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/audit?page=1&limit=20` | Paginated compliance audit history | Bearer Token |
| `GET` | `/api/audit/:id` | Full audit details including JSONB findings | Bearer Token |
