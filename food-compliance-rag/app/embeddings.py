"""
Embedding generation — supports:
1. FastEmbed (Free, local ONNX CPU inference, no API keys needed, 384d by default)
2. OpenAI (Paid API, text-embedding-3-small, 1536d)
"""

from __future__ import annotations

import logging
import time
from typing import Sequence

from app.config import get_settings

logger = logging.getLogger(__name__)

# Default dimension for free local FastEmbed (BAAI/bge-small-en-v1.5)
EMBEDDING_DIM = 384

_fastembed_model = None


def _get_fastembed_model():
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding
        settings = get_settings()
        logger.info("Loading local FastEmbed model: %s (100%% FREE, no API key required)", settings.fastembed_model)
        _fastembed_model = TextEmbedding(model_name=settings.fastembed_model)
    return _fastembed_model


def _get_openai_client():
    import openai
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set in .env. "
            "To use the 100% free local embeddings instead, set EMBEDDING_PROVIDER=fastembed in your .env file."
        )
    return openai.OpenAI(api_key=settings.openai_api_key)


def generate_embedding(text: str) -> list[float]:
    """Generate a single embedding vector using the configured provider."""
    settings = get_settings()
    text = text.replace("\n", " ").strip()

    if settings.embedding_provider == "fastembed":
        if not text:
            return [0.0] * settings.embedding_dimension
        model = _get_fastembed_model()
        vec = list(model.embed([text]))[0]
        return [float(v) for v in vec]

    # OpenAI provider
    import openai
    client = _get_openai_client()
    if not text:
        return [0.0] * settings.embedding_dimension

    resp = client.embeddings.create(
        input=[text],
        model=settings.openai_embedding_model,
    )
    vec = resp.data[0].embedding
    return [float(v) for v in vec]


def generate_embeddings_batch(
    texts: Sequence[str],
    batch_size: int = 64,
    max_retries: int = 3,
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    For FastEmbed: executes fast local batch ONNX inference.
    For OpenAI: executes API batches with rate-limit retry backoff.
    """
    settings = get_settings()

    if settings.embedding_provider == "fastembed":
        model = _get_fastembed_model()
        cleaned = [t.replace("\n", " ").strip() or "empty" for t in texts]
        results = []
        for emb in model.embed(cleaned, batch_size=batch_size):
            results.append([float(v) for v in emb])
        logger.info("Generated %d embeddings using FastEmbed", len(results))
        return results

    # OpenAI provider
    import openai
    client = _get_openai_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = [t.replace("\n", " ").strip() or "empty" for t in texts[i : i + batch_size]]

        for attempt in range(max_retries):
            try:
                resp = client.embeddings.create(
                    input=batch,
                    model=settings.openai_embedding_model,
                )
                vecs = [[float(v) for v in d.embedding] for d in resp.data]
                all_embeddings.extend(vecs)
                break
            except openai.RateLimitError:
                wait = 2 ** attempt * 5
                logger.warning(
                    "OpenAI rate limit hit, retrying in %ds (attempt %d/%d)",
                    wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
            except openai.APIError as exc:
                if attempt == max_retries - 1:
                    raise
                logger.warning("OpenAI API error: %s — retrying", exc)
                time.sleep(2)

        done = min(i + batch_size, len(texts))
        logger.info("Embedded %d / %d texts via OpenAI", done, len(texts))

    return all_embeddings
