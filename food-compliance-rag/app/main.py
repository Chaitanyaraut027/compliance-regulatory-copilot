"""
FastAPI application — Food Regulatory Compliance RAG API.
"""

from __future__ import annotations

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import check_connection, close_pool
from app.schemas import (
    HealthResponse,
    DocumentOut,
    IngestRequest,
    IngestResult,
    SearchRequest,
    SearchResponse,
    ChunkResult,
    ComplianceRequest,
    ComplianceResponse,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    logger.info("Food Compliance RAG API starting up...")
    yield
    close_pool()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Food Regulatory Compliance RAG API",
    description=(
        "RAG-powered API for FSSAI regulatory compliance assessment. "
        "Ingests regulatory PDFs, generates embeddings, and compares "
        "company evidence against retrieved regulatory requirements."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.responses import HTMLResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    """Interactive Web Dashboard for testing the Compliance RAG pipeline."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FSSAI Food Regulatory Compliance Copilot</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --border: #334155;
      --green: #22c55e;
      --orange: #f59e0b;
      --red: #ef4444;
      --blue: #3b82f6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 2rem 1rem; }
    .container { max-width: 1000px; margin: 0 auto; }
    header { margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; }
    h1 { font-size: 1.8rem; font-weight: 700; color: #fff; }
    .subtitle { color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }
    .nav-links a { color: var(--primary); text-decoration: none; font-weight: 500; font-size: 0.95rem; margin-left: 1rem; border: 1px solid var(--primary); padding: 0.4rem 0.8rem; border-radius: 6px; transition: all 0.2s; }
    .nav-links a:hover { background: var(--primary); color: #000; }
    .tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
    .tab-btn { background: var(--card-bg); border: 1px solid var(--border); color: var(--muted); padding: 0.6rem 1.2rem; border-radius: 8px; cursor: pointer; font-size: 0.95rem; font-weight: 500; }
    .tab-btn.active { background: var(--primary); color: #000; border-color: var(--primary); font-weight: 600; }
    .panel { display: none; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }
    .panel.active { display: block; }
    .form-group { margin-bottom: 1.25rem; }
    label { display: block; margin-bottom: 0.5rem; font-weight: 500; font-size: 0.9rem; }
    input, textarea, select { width: 100%; padding: 0.75rem; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; color: #fff; font-size: 0.95rem; font-family: inherit; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: var(--primary); }
    button.btn-submit { background: var(--primary); color: #000; border: none; padding: 0.75rem 1.5rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
    button.btn-submit:hover { background: var(--primary-hover); }
    .result-box { margin-top: 1.5rem; padding: 1rem; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; font-family: inherit; white-space: pre-wrap; font-size: 0.9rem; }
    .badge { display: inline-block; padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem; }
    .badge-COMPLIANT { background: rgba(34, 197, 94, 0.2); color: var(--green); border: 1px solid var(--green); }
    .badge-PARTIALLY_COMPLIANT { background: rgba(245, 158, 11, 0.2); color: var(--orange); border: 1px solid var(--orange); }
    .badge-MISSING_EVIDENCE { background: rgba(59, 130, 246, 0.2); color: var(--blue); border: 1px solid var(--blue); }
    .badge-POTENTIALLY_NON_COMPLIANT { background: rgba(239, 68, 68, 0.2); color: var(--red); border: 1px solid var(--red); }
    .badge-NEEDS_REVIEW { background: rgba(148, 163, 184, 0.2); color: var(--muted); border: 1px solid var(--muted); }
    .chunk-card { background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .chunk-header { display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--primary); margin-bottom: 0.5rem; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>🛡️ Food Regulatory Compliance Copilot</h1>
        <div class="subtitle">FSSAI Retrieval-Augmented Generation (RAG) Architecture</div>
      </div>
      <div class="nav-links">
        <a href="/docs" target="_blank">Swagger API Docs ↗</a>
      </div>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="showTab('status')">System Health</button>
      <button class="tab-btn" onclick="showTab('search')">Semantic Search</button>
      <button class="tab-btn" onclick="showTab('compliance')">Compliance Assessment</button>
      <button class="tab-btn" onclick="showTab('ingest')">PDF Ingestion</button>
    </div>

    <!-- Health Tab -->
    <div id="panel-status" class="panel active">
      <h2>System Status & Diagnostics</h2>
      <p style="color: var(--muted); margin: 0.5rem 0 1rem 0;">Real-time health report for PostgreSQL, pgvector, and OpenAI configuration.</p>
      <button class="btn-submit" onclick="fetchHealth()">Check System Health</button>
      <div id="health-result" class="result-box" style="display:none;"></div>
    </div>

    <!-- Search Tab -->
    <div id="panel-search" class="panel">
      <h2>Regulatory Semantic Search</h2>
      <p style="color: var(--muted); margin: 0.5rem 0 1rem 0;">Retrieve top-5 matching regulatory clauses directly from pgvector embeddings.</p>
      <div class="form-group">
        <label>Query</label>
        <input type="text" id="search-query" value="What hygiene records should a food facility maintain?">
      </div>
      <button class="btn-submit" onclick="runSearch()">Search Regulations</button>
      <div id="search-result" style="margin-top: 1.5rem;"></div>
    </div>

    <!-- Compliance Tab -->
    <div id="panel-compliance" class="panel">
      <h2>RAG Compliance Assessment</h2>
      <p style="color: var(--muted); margin: 0.5rem 0 1rem 0;">Compare company policies against retrieved FSSAI regulatory requirements.</p>
      <div class="form-group">
        <label>Compliance Question / Requirement</label>
        <input type="text" id="comp-q" value="What mandatory labelling elements must appear on pre-packaged food containers?">
      </div>
      <div class="form-group">
        <label>Compliance Area</label>
        <select id="comp-area">
          <option>General Labelling & Display</option>
          <option>Contaminants & Residues</option>
          <option>Food Additives</option>
          <option>Licensing & Registration</option>
          <option>Hygiene & Sanitary Practices</option>
        </select>
      </div>
      <div class="form-group">
        <label>Company Policy / Evidence Excerpt</label>
        <textarea id="comp-evidence" rows="4">Our facility labels all consumer food packages with: Brand Name, Ingredients List in descending order of weight, Net Quantity, Batch Identification, Manufacturing Date, Expiry Date, Manufacturer Address, and FSSAI License Number.</textarea>
      </div>
      <button class="btn-submit" onclick="runCompliance()">Assess Compliance</button>
      <div id="comp-result" style="margin-top: 1.5rem;"></div>
    </div>

    <!-- Ingest Tab -->
    <div id="panel-ingest" class="panel">
      <h2>PDF Ingestion Pipeline</h2>
      <p style="color: var(--muted); margin: 0.5rem 0 1rem 0;">Extracts text page-by-page from data/regulations/, chunks content, generates OpenAI embeddings, and persists in Supabase pgvector.</p>
      <button class="btn-submit" onclick="runIngest()">Trigger Document Ingestion</button>
      <div id="ingest-result" class="result-box" style="display:none;"></div>
    </div>
  </div>

  <script>
    function showTab(name) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById('panel-' + name).classList.add('active');
    }

    async function fetchHealth() {
      const box = document.getElementById('health-result');
      box.style.display = 'block';
      box.innerText = 'Checking health...';
      try {
        const res = await fetch('/health');
        const data = await res.json();
        box.innerText = JSON.stringify(data, null, 2);
      } catch (err) {
        box.innerText = 'Error: ' + err.message;
      }
    }

    async function runSearch() {
      const container = document.getElementById('search-result');
      container.innerHTML = '<div class="result-box">Retrieving matching regulatory chunks from pgvector...</div>';
      try {
        const query = document.getElementById('search-query').value;
        const res = await fetch('/search', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query: query, top_k: 5})
        });
        const data = await res.json();
        if (data.results && data.results.length > 0) {
          let html = '';
          data.results.forEach(r => {
            html += `
              <div class="chunk-card">
                <div class="chunk-header">
                  <span><strong>${r.doc_title || r.doc_filename}</strong> (pp. ${r.page_start}–${r.page_end})</span>
                  <span>Similarity: ${(r.similarity || 0).toFixed(4)}</span>
                </div>
                ${r.section_title ? '<div style="font-size:0.85rem; color:#f59e0b; margin-bottom:0.4rem;">Section: ' + r.section_title + '</div>' : ''}
                <div style="font-size:0.9rem; line-height:1.5;">${r.content}</div>
              </div>
            `;
          });
          container.innerHTML = html;
        } else {
          container.innerHTML = '<div class="result-box">No matching regulatory passages found or database not yet ingested.</div>';
        }
      } catch (err) {
        container.innerHTML = '<div class="result-box" style="color:var(--red);">Error: ' + err.message + '</div>';
      }
    }

    async function runCompliance() {
      const container = document.getElementById('comp-result');
      container.innerHTML = '<div class="result-box">Performing RAG retrieval and compliance evaluation...</div>';
      try {
        const body = {
          question: document.getElementById('comp-q').value,
          compliance_area: document.getElementById('comp-area').value,
          company_evidence: document.getElementById('comp-evidence').value,
          top_k: 5
        };
        const res = await fetch('/compliance/check', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body)
        });
        const data = await res.json();
        const badgeClass = 'badge-' + (data.overall_status || 'NEEDS_REVIEW');
        let html = `
          <div class="chunk-card" style="border-left: 4px solid var(--primary);">
            <div class="badge ${badgeClass}">${data.overall_status}</div>
            <h3 style="margin: 0.5rem 0;">${data.summary || 'Assessment Summary'}</h3>
            <p style="font-size:0.85rem; color:var(--muted); margin-bottom:1rem;">${data.disclaimer}</p>
          </div>
        `;
        if (data.findings && data.findings.length > 0) {
          html += '<h3 style="margin:1.5rem 0 0.8rem 0;">Detailed Requirements Breakdown:</h3>';
          data.findings.forEach(f => {
            const fBadge = 'badge-' + (f.status || 'NEEDS_REVIEW');
            html += `
              <div class="chunk-card">
                <div class="badge ${fBadge}">${f.status}</div>
                <div style="font-weight:600; font-size:1rem; margin-bottom:0.5rem;">${f.requirement}</div>
                <p style="margin-bottom:0.5rem; font-size:0.9rem;">${f.explanation}</p>
                ${f.evidence_found && f.evidence_found.length ? '<div style="color:var(--green); font-size:0.85rem;">✔ Evidence Found: ' + f.evidence_found.join(', ') + '</div>' : ''}
                ${f.evidence_missing && f.evidence_missing.length ? '<div style="color:var(--orange); font-size:0.85rem; margin-top:0.25rem;">⚠ Evidence Missing: ' + f.evidence_missing.join(', ') + '</div>' : ''}
              </div>
            `;
          });
        }
        container.innerHTML = html;
      } catch (err) {
        container.innerHTML = '<div class="result-box" style="color:var(--red);">Error: ' + err.message + '</div>';
      }
    }

    async function runIngest() {
      const box = document.getElementById('ingest-result');
      box.style.display = 'block';
      box.innerText = 'Triggering PDF ingestion pipeline...';
      try {
        const res = await fetch('/ingest', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        const data = await res.json();
        box.innerText = JSON.stringify(data, null, 2);
      } catch (err) {
        box.innerText = 'Error: ' + err.message;
      }
    }
  </script>
</body>
</html>
"""


# ── Health ────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Check application configuration and database connectivity."""
    settings = get_settings()
    reg_path = settings.regulations_path
    pdf_count = len(list(reg_path.glob("*.pdf"))) if reg_path.is_dir() else 0

    db_info = None
    try:
        db_info = check_connection()
    except Exception as exc:
        db_info = {"status": "error", "detail": str(exc)}

    return HealthResponse(
        status="ok" if db_info and db_info.get("status") == "connected" else "degraded",
        database=db_info,
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
        groq_configured=bool(settings.groq_api_key),
        openai_configured=bool(settings.openai_api_key),
        regulations_dir_exists=reg_path.is_dir(),
        pdf_count=pdf_count,
    )


# ── Documents ─────────────────────────────────────────────────

@app.get("/documents", response_model=list[DocumentOut], tags=["Documents"])
def list_documents():
    """List all indexed regulatory documents."""
    from app.vector_store import list_documents as vs_list
    try:
        docs = vs_list()
        return [DocumentOut(**d) for d in docs]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Ingestion ─────────────────────────────────────────────────

@app.post("/ingest", response_model=IngestResult, tags=["Ingestion"])
def ingest(req: IngestRequest | None = None):
    """Trigger PDF ingestion pipeline."""
    from app.ingest import ingest_directory

    directory = None
    if req and req.directory:
        directory = Path(req.directory)

    try:
        result = ingest_directory(directory)
        return result
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Search ────────────────────────────────────────────────────

@app.post("/search", response_model=SearchResponse, tags=["Search"])
def search(req: SearchRequest):
    """Semantic search over indexed regulatory content."""
    from app.retriever import retrieve

    try:
        results = retrieve(
            query=req.query,
            top_k=req.top_k,
            document_id=req.document_id,
        )

        chunks = [
            ChunkResult(
                chunk_id=r["id"],
                document_id=r["document_id"],
                doc_filename=r.get("doc_filename", ""),
                doc_title=r.get("doc_title"),
                chunk_index=r.get("chunk_index", 0),
                content=r["content"],
                page_start=r.get("page_start"),
                page_end=r.get("page_end"),
                section_title=r.get("section_title"),
                similarity=r.get("similarity", 0.0),
            )
            for r in results
        ]

        return SearchResponse(
            query=req.query,
            results=chunks,
            total=len(chunks),
        )
    except Exception as exc:
        logger.error("Search failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Compliance ────────────────────────────────────────────────

@app.post(
    "/compliance/check",
    response_model=ComplianceResponse,
    tags=["Compliance"],
)
def compliance_check(req: ComplianceRequest):
    """
    Assess company evidence against retrieved FSSAI regulatory requirements.
    """
    from app.compliance import assess_compliance

    try:
        return assess_compliance(req)
    except Exception as exc:
        logger.error("Compliance check failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
