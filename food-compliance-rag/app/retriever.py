"""
Retriever — combines embedding + pgvector search.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.embeddings import generate_embedding
from app.vector_store import search_similar_chunks
from app.config import get_settings

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    top_k: int | None = None,
    document_id: UUID | None = None,
) -> list[dict]:
    """
    End-to-end retrieval:
    1. Embed the query
    2. Search pgvector for most similar chunks
    3. Return results with metadata
    """
    settings = get_settings()
    top_k = top_k or settings.retrieval_top_k

    logger.info("Retrieving top-%d chunks for: %.80s...", top_k, query)

    query_embedding = generate_embedding(query)
    results = search_similar_chunks(
        query_embedding=query_embedding,
        top_k=top_k,
        document_id=document_id,
    )

    if not results:
        logger.info("No results found for query.")
    else:
        logger.info(
            "Retrieved %d chunks (best similarity: %.4f)",
            len(results),
            results[0].get("similarity", 0),
        )

    return results
