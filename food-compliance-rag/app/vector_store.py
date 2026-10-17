"""
Vector store — Supabase PostgreSQL + pgvector persistence layer.
"""

from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from app.database import get_connection

logger = logging.getLogger(__name__)


# ── Document CRUD ─────────────────────────────────────────────

def upsert_document(
    filename: str,
    file_hash: str,
    title: str | None = None,
    source_url: str | None = None,
    publication_date: str | None = None,
    version_info: str | None = None,
    page_count: int | None = None,
    metadata: dict | None = None,
) -> tuple[UUID, bool]:
    """
    Insert or update a document row.

    Returns (document_id, is_new).
    If the file_hash matches an existing record, the document is considered
    unchanged and is_new=False.
    """
    with get_connection() as conn:
        # Check if this filename already exists
        existing = conn.execute(
            "SELECT id, file_hash FROM documents WHERE filename = %s",
            (filename,),
        ).fetchone()

        if existing:
            if existing["file_hash"] == file_hash:
                logger.info("Document %s unchanged — skipping.", filename)
                return UUID(str(existing["id"])), False
            # File changed — update metadata
            conn.execute(
                """
                UPDATE documents
                SET file_hash = %s, title = %s, source_url = %s,
                    publication_date = %s, version_info = %s,
                    page_count = %s, metadata = %s
                WHERE id = %s
                """,
                (
                    file_hash, title, source_url, publication_date,
                    version_info, page_count,
                    json.dumps(metadata or {}),
                    str(existing["id"]),
                ),
            )
            # Remove old chunks so new ones can be inserted
            conn.execute(
                "DELETE FROM document_chunks WHERE document_id = %s",
                (str(existing["id"]),),
            )
            conn.commit()
            logger.info("Document %s updated — old chunks removed.", filename)
            return UUID(str(existing["id"])), True

        # New document
        row = conn.execute(
            """
            INSERT INTO documents
                (filename, file_hash, title, source_url,
                 publication_date, version_info, page_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                filename, file_hash, title, source_url,
                publication_date, version_info, page_count,
                json.dumps(metadata or {}),
            ),
        ).fetchone()
        conn.commit()
        doc_id = UUID(str(row["id"]))
        logger.info("Document %s inserted → %s", filename, doc_id)
        return doc_id, True


# ── Chunk persistence ─────────────────────────────────────────

def insert_chunks(
    document_id: UUID,
    chunks: list[dict],
    batch_size: int = 100,
) -> tuple[int, int]:
    """
    Insert chunks with embeddings using high-speed batching.

    Returns (inserted, skipped).
    """
    if not chunks:
        return 0, 0

    inserted = 0
    skipped = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                params = [
                    (
                        str(document_id),
                        ch["chunk_index"],
                        ch["content"],
                        "[" + ",".join(str(v) for v in ch["embedding"]) + "]",
                        ch["page_start"],
                        ch["page_end"],
                        ch.get("section_title"),
                        json.dumps(ch.get("metadata", {})),
                        ch["content_hash"],
                    )
                    for ch in batch
                ]
                try:
                    cur.executemany(
                        """
                        INSERT INTO document_chunks
                            (document_id, chunk_index, content, embedding,
                             page_start, page_end, section_title,
                             metadata, content_hash)
                        VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id, content_hash) DO NOTHING
                        """,
                        params,
                    )
                    inserted += len(batch)
                except Exception as exc:
                    logger.warning("Batch insert error at %d: %s", i, exc)
                    skipped += len(batch)
        conn.commit()

    return inserted, skipped


# ── Retrieval ─────────────────────────────────────────────────

def search_similar_chunks(
    query_embedding: list[float],
    top_k: int = 5,
    document_id: UUID | None = None,
) -> list[dict]:
    """
    Semantic search via the match_document_chunks SQL function.
    """
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM match_document_chunks(
                %s::vector, %s, %s::uuid
            )
            """,
            (
                embedding_str,
                top_k,
                str(document_id) if document_id else None,
            ),
        ).fetchall()

    return [dict(r) for r in rows]


# ── Listing ───────────────────────────────────────────────────

def list_documents() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT d.*, 
                   (SELECT count(*) FROM document_chunks dc WHERE dc.document_id = d.id)
                   AS chunk_count
            FROM documents d
            ORDER BY d.ingested_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_document_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT count(*) AS cnt FROM documents").fetchone()
    return row["cnt"]


def get_chunk_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT count(*) AS cnt FROM document_chunks").fetchone()
    return row["cnt"]
