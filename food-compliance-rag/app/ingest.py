"""
Ingestion pipeline — orchestrates PDF extraction → chunking → embedding → storage.

Can be run as:  python -m app.ingest
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.config import get_settings
from app.pdf_extractor import extract_all_pdfs
from app.chunker import chunk_pages
from app.embeddings import generate_embeddings_batch
from app.vector_store import upsert_document, insert_chunks
from app.schemas import IngestResult

logger = logging.getLogger(__name__)


def ingest_directory(directory: Path | None = None) -> IngestResult:
    """
    Full ingestion pipeline:
    1. Extract text from all PDFs.
    2. Chunk each document.
    3. Generate embeddings in batch.
    4. Store documents and chunks in Supabase.
    """
    settings = get_settings()
    directory = directory or settings.regulations_path
    result = IngestResult()

    logger.info("Starting ingestion from: %s", directory)

    # ── Step 1: Extract ──
    docs = extract_all_pdfs(directory)
    if not docs:
        result.errors.append(f"No PDFs found in {directory}")
        return result

    for doc in docs:
        if doc.error:
            result.errors.append(f"{doc.filename}: {doc.error}")
            continue
        if doc.is_empty:
            result.errors.append(
                f"{doc.filename}: Empty/scanned PDF — no text extracted "
                f"({doc.page_count} pages)"
            )
            continue

        try:
            # ── Step 2: Upsert document ──
            doc_id, is_new = upsert_document(
                filename=doc.filename,
                file_hash=doc.file_hash,
                title=doc.title,
                publication_date=doc.publication_date,
                page_count=doc.page_count,
            )

            if not is_new:
                logger.info("Skipping %s — unchanged.", doc.filename)
                continue

            # ── Step 3: Chunk ──
            pages = [
                {"page_number": p.page_number, "text": p.text}
                for p in doc.pages
                if p.text.strip()
            ]
            chunks = chunk_pages(pages)
            if not chunks:
                result.errors.append(f"{doc.filename}: No chunks produced.")
                continue

            logger.info(
                "%s → %d pages, %d chunks", doc.filename, len(pages), len(chunks)
            )

            # ── Step 4: Embed ──
            texts = [c.content for c in chunks]
            embeddings = generate_embeddings_batch(texts)

            # ── Step 5: Store ──
            chunk_dicts = []
            for c, emb in zip(chunks, embeddings):
                chunk_dicts.append({
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "embedding": emb,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                    "section_title": c.section_title,
                    "content_hash": c.content_hash,
                    "metadata": {
                        "filename": doc.filename,
                        "title": doc.title,
                    },
                })

            inserted, skipped = insert_chunks(doc_id, chunk_dicts)
            result.documents_processed += 1
            result.chunks_created += inserted
            result.chunks_skipped += skipped

            logger.info(
                "%s: %d chunks inserted, %d skipped",
                doc.filename, inserted, skipped,
            )

        except Exception as exc:
            msg = f"{doc.filename}: {exc}"
            logger.error("Ingestion error: %s", msg, exc_info=True)
            result.errors.append(msg)

    logger.info(
        "Ingestion complete: %d docs, %d chunks, %d skipped, %d errors",
        result.documents_processed,
        result.chunks_created,
        result.chunks_skipped,
        len(result.errors),
    )
    return result


# ── CLI entry point ───────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    directory = None
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])

    result = ingest_directory(directory)

    print("\n═══ Ingestion Summary ═══")
    print(f"  Documents processed : {result.documents_processed}")
    print(f"  Chunks created      : {result.chunks_created}")
    print(f"  Chunks skipped      : {result.chunks_skipped}")
    if result.errors:
        print(f"  Errors ({len(result.errors)}):")
        for e in result.errors:
            print(f"    ⚠  {e}")
    else:
        print("  Errors              : None")


if __name__ == "__main__":
    main()
