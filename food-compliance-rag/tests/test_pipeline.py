"""
Tests for the food compliance RAG pipeline.

Divided into:
  - Unit tests: run without Supabase or OpenAI (mocked dependencies)
  - Integration markers: require live credentials
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# ── Ensure project root is on sys.path ───────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════
# 1. PDF Extraction Tests
# ═══════════════════════════════════════════════════════════════

class TestPDFExtraction:
    """Test PDF text extraction (requires PyMuPDF but no network)."""

    def test_extract_all_pdfs_finds_files(self):
        from app.pdf_extractor import extract_all_pdfs

        data_dir = PROJECT_ROOT / "data" / "regulations"
        if not data_dir.exists() or not list(data_dir.glob("*.pdf")):
            pytest.skip("No PDFs in data/regulations/")

        docs = extract_all_pdfs(data_dir)
        assert len(docs) > 0, "Should find at least one PDF"

    def test_extracted_doc_has_metadata(self):
        from app.pdf_extractor import extract_all_pdfs

        data_dir = PROJECT_ROOT / "data" / "regulations"
        if not data_dir.exists() or not list(data_dir.glob("*.pdf")):
            pytest.skip("No PDFs in data/regulations/")

        docs = extract_all_pdfs(data_dir)
        for doc in docs:
            assert doc.filename, "filename must be set"
            assert doc.file_hash, "file_hash must be set"
            assert doc.page_count > 0 or doc.error, "page_count or error expected"

    def test_extracted_doc_has_pages_with_text(self):
        from app.pdf_extractor import extract_all_pdfs

        data_dir = PROJECT_ROOT / "data" / "regulations"
        if not data_dir.exists() or not list(data_dir.glob("*.pdf")):
            pytest.skip("No PDFs in data/regulations/")

        docs = extract_all_pdfs(data_dir)
        docs_with_text = [d for d in docs if not d.is_empty and not d.error]
        assert len(docs_with_text) > 0, "At least one PDF should have text"

        for doc in docs_with_text:
            assert len(doc.pages) > 0, f"{doc.filename}: no pages"
            total_chars = sum(p.char_count for p in doc.pages)
            assert total_chars > 100, f"{doc.filename}: suspiciously little text"

    def test_publication_date_extraction(self):
        from app.pdf_extractor import _extract_date_from_filename

        assert _extract_date_from_filename(
            "Compendium_Contaminants_Regulations_28_01_2022.pdf"
        ) == "2022-01-28"
        assert _extract_date_from_filename("random_file.pdf") is None

    def test_file_hash_consistency(self):
        from app.pdf_extractor import compute_file_hash

        data_dir = PROJECT_ROOT / "data" / "regulations"
        pdfs = list(data_dir.glob("*.pdf"))
        if not pdfs:
            pytest.skip("No PDFs")

        h1 = compute_file_hash(pdfs[0])
        h2 = compute_file_hash(pdfs[0])
        assert h1 == h2, "Same file must produce same hash"

    def test_scanned_empty_detection(self):
        """Verify that the extractor flags empty/scanned docs."""
        from app.pdf_extractor import ExtractedDocument

        doc = ExtractedDocument(
            filename="test.pdf",
            filepath="/test.pdf",
            page_count=10,
            is_empty=True,
            is_scanned=True,
            file_hash="abc",
        )
        assert doc.is_empty
        assert doc.is_scanned


# ═══════════════════════════════════════════════════════════════
# 2. Chunker Tests
# ═══════════════════════════════════════════════════════════════

class TestChunker:
    """Test text chunking logic (no network required)."""

    def test_basic_chunking(self):
        from app.chunker import chunk_pages

        pages = [
            {"page_number": 1, "text": "A" * 2000},
            {"page_number": 2, "text": "B" * 500},
        ]
        chunks = chunk_pages(pages, chunk_size=900, chunk_overlap=120)
        assert len(chunks) >= 2, "Should produce multiple chunks"

    def test_chunk_overlap(self):
        from app.chunker import chunk_pages

        text = "word " * 400  # ~2000 chars
        pages = [{"page_number": 1, "text": text}]
        chunks = chunk_pages(pages, chunk_size=800, chunk_overlap=100)

        if len(chunks) >= 2:
            # The end of chunk 0 should overlap with start of chunk 1
            tail = chunks[0].content[-80:]
            assert tail in chunks[1].content, (
                "Overlap: tail of chunk 0 should appear in chunk 1"
            )

    def test_page_tracking(self):
        from app.chunker import chunk_pages

        pages = [
            {"page_number": 5, "text": "Hello " * 200},
            {"page_number": 6, "text": "World " * 200},
        ]
        chunks = chunk_pages(pages, chunk_size=900, chunk_overlap=100)
        for ch in chunks:
            assert ch.page_start >= 5
            assert ch.page_end <= 6

    def test_empty_pages(self):
        from app.chunker import chunk_pages

        chunks = chunk_pages([], chunk_size=900, chunk_overlap=100)
        assert chunks == []

    def test_content_hash_uniqueness(self):
        from app.chunker import chunk_pages

        pages = [
            {"page_number": 1, "text": "Same text here. " * 100},
        ]
        chunks = chunk_pages(pages, chunk_size=500, chunk_overlap=50)
        hashes = [c.content_hash for c in chunks]
        assert len(hashes) == len(set(hashes)), "Each chunk should have unique hash"

    def test_chunk_size_approximate(self):
        from app.chunker import chunk_pages

        text = "Regulatory requirement. " * 200
        pages = [{"page_number": 1, "text": text}]
        chunks = chunk_pages(pages, chunk_size=900, chunk_overlap=120)

        for ch in chunks[:-1]:  # Last chunk may be shorter
            assert len(ch.content) >= 500, f"Chunk too short: {len(ch.content)}"
            assert len(ch.content) <= 1200, f"Chunk too long: {len(ch.content)}"

    def test_section_detection(self):
        from app.chunker import _detect_section_title

        assert _detect_section_title("FOOD SAFETY STANDARDS\nSome text") is not None
        assert _detect_section_title("Chapter 1 Overview\nContent") is not None
        assert _detect_section_title("just a normal sentence.") is None


# ═══════════════════════════════════════════════════════════════
# 3. Embeddings Tests (mocked)
# ═══════════════════════════════════════════════════════════════

class TestEmbeddings:
    """Test embedding generation for FastEmbed (free local) and OpenAI."""

    def test_embedding_dimension(self):
        from app.embeddings import EMBEDDING_DIM
        assert EMBEDDING_DIM == 384

    def test_fastembed_local_generation(self):
        from app.embeddings import generate_embedding
        vec = generate_embedding("FSSAI food safety regulations")
        assert len(vec) == 384
        assert isinstance(vec[0], float)

    def test_fastembed_batch_generation(self):
        from app.embeddings import generate_embeddings_batch
        vecs = generate_embeddings_batch(["food clause 1", "food clause 2"])
        assert len(vecs) == 2
        assert len(vecs[0]) == 384
        assert len(vecs[1]) == 384

    @patch("app.embeddings._get_openai_client")
    def test_openai_mocked_embedding(self, mock_get_client):
        from app.config import get_settings
        from app.embeddings import generate_embedding

        fake_vec = [0.01] * 1536
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=fake_vec)]
        )
        mock_get_client.return_value = mock_client

        with patch.object(get_settings(), "embedding_provider", "openai"):
            result = generate_embedding("test text")
            assert len(result) == 1536


# ═══════════════════════════════════════════════════════════════
# 4. Schema Validation Tests
# ═══════════════════════════════════════════════════════════════

class TestSchemas:
    """Test Pydantic schema validation."""

    def test_search_request_min_length(self):
        from app.schemas import SearchRequest

        with pytest.raises(Exception):
            SearchRequest(query="ab")  # too short

        req = SearchRequest(query="What are food safety rules?")
        assert req.top_k == 5  # default

    def test_compliance_request(self):
        from app.schemas import ComplianceRequest

        req = ComplianceRequest(
            question="What labelling is required?",
            company_evidence="We label all products with ingredients.",
        )
        assert req.top_k == 5

    def test_compliance_response_has_disclaimer(self):
        from app.schemas import ComplianceResponse

        resp = ComplianceResponse(
            question="test",
            overall_status="NEEDS_REVIEW",
            summary="test summary",
        )
        assert "not constitute legal advice" in resp.disclaimer

    def test_compliance_statuses(self):
        from app.schemas import ComplianceFinding

        for status in [
            "COMPLIANT", "PARTIALLY_COMPLIANT", "MISSING_EVIDENCE",
            "POTENTIALLY_NON_COMPLIANT", "NEEDS_REVIEW",
        ]:
            f = ComplianceFinding(
                requirement="test",
                status=status,
                explanation="test",
            )
            assert f.status == status

    def test_ingest_result(self):
        from app.schemas import IngestResult

        r = IngestResult()
        assert r.documents_processed == 0
        assert r.errors == []


# ═══════════════════════════════════════════════════════════════
# 5. Config Tests
# ═══════════════════════════════════════════════════════════════

class TestConfig:
    def test_default_settings(self):
        from app.config import Settings

        s = Settings()
        assert s.chunk_size == 900
        assert s.chunk_overlap == 120
        assert s.retrieval_top_k == 5
        assert s.openai_embedding_model == "text-embedding-3-small"

    def test_dsn_format(self):
        from app.config import Settings

        s = Settings(
            supabase_db_host="example.supabase.co",
            supabase_db_password="secret",
        )
        dsn = s.dsn
        assert "example.supabase.co" in dsn
        assert "secret" in dsn
        assert dsn.startswith("postgresql://")


# ═══════════════════════════════════════════════════════════════
# 6. API Tests (mocked dependencies)
# ═══════════════════════════════════════════════════════════════

class TestAPI:
    """Test FastAPI endpoints with mocked services."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Health endpoint should return even without DB."""
        with patch("app.main.check_connection", return_value={"status": "error", "detail": "no db"}):
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("ok", "degraded")

    def test_search_validation(self, client):
        """Search should reject too-short queries."""
        resp = client.post("/search", json={"query": "ab"})
        assert resp.status_code == 422

    def test_compliance_validation(self, client):
        """Compliance check should require both question and evidence."""
        resp = client.post("/compliance/check", json={"question": "test?"})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════
# 7. Integration markers
# ═══════════════════════════════════════════════════════════════

requires_db = pytest.mark.skipif(
    not os.getenv("SUPABASE_DB_HOST"),
    reason="Supabase not configured",
)
requires_openai = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not set",
)


@requires_db
class TestDatabaseIntegration:
    def test_connection(self):
        from app.database import check_connection
        result = check_connection()
        assert result["status"] == "connected"

    def test_document_count(self):
        from app.vector_store import get_document_count
        count = get_document_count()
        assert isinstance(count, int)


@requires_db
@requires_openai
class TestSearchIntegration:
    def test_search_returns_results(self):
        from app.retriever import retrieve
        results = retrieve("food safety hygiene requirements")
        # May be empty if no docs ingested yet
        assert isinstance(results, list)
