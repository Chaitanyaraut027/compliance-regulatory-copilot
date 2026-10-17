-- ============================================================
-- Food Regulatory Compliance RAG — Supabase PostgreSQL Schema
-- Execute this entire script in the Supabase SQL Editor.
-- ============================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Documents table — one row per ingested PDF
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        TEXT NOT NULL UNIQUE,
    title           TEXT,
    source_url      TEXT,
    publication_date TEXT,
    version_info    TEXT,
    page_count      INTEGER,
    file_hash       TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 3. Document chunks table — stores text chunks with embeddings
-- NOTE: Default dimension is 384 for the 100% FREE FastEmbed model (BAAI/bge-small-en-v1.5).
-- If you choose to use paid OpenAI text-embedding-3-small, change vector(384) to vector(1536).
CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(384),
    page_start      INTEGER,
    page_end        INTEGER,
    section_title   TEXT,
    metadata        JSONB DEFAULT '{}',
    content_hash    TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),

    -- Prevent duplicate chunks within the same document
    CONSTRAINT uq_document_chunk UNIQUE (document_id, content_hash)
);

-- 4. Indexes for performance

-- Fast lookup of chunks by document
CREATE INDEX IF NOT EXISTS idx_chunks_document_id
    ON document_chunks(document_id);

-- Fast lookup by content hash (idempotent ingestion)
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash
    ON document_chunks(content_hash);

-- JSONB metadata index
CREATE INDEX IF NOT EXISTS idx_chunks_metadata
    ON document_chunks USING GIN (metadata);

-- Document filename lookup
CREATE INDEX IF NOT EXISTS idx_documents_filename
    ON documents(filename);

-- 5. Vector similarity index (IVFFlat for cosine distance)
--    Use 'lists' = sqrt(N) as a starting point. For < 10k rows, 100 lists is fine.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 6. Semantic similarity search function
--    Uses cosine distance operator (<=>).
--    Returns chunks ordered by similarity (lowest distance = most similar).
--    NOTE: vector(384) for Free FastEmbed. Use vector(1536) if using OpenAI.
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding     vector(384),
    match_count         INTEGER DEFAULT 5,
    filter_document_id  UUID DEFAULT NULL
)
RETURNS TABLE (
    id              UUID,
    document_id     UUID,
    chunk_index     INTEGER,
    content         TEXT,
    page_start      INTEGER,
    page_end        INTEGER,
    section_title   TEXT,
    metadata        JSONB,
    similarity      FLOAT,
    doc_filename    TEXT,
    doc_title       TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.content,
        dc.page_start,
        dc.page_end,
        dc.section_title,
        dc.metadata,
        -- Cosine similarity = 1 - cosine distance
        (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity,
        d.filename  AS doc_filename,
        d.title     AS doc_title
    FROM document_chunks dc
    JOIN documents d ON d.id = dc.document_id
    WHERE
        dc.embedding IS NOT NULL
        AND (filter_document_id IS NULL OR dc.document_id = filter_document_id)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 7. Helper: update the updated_at timestamp on documents
CREATE OR REPLACE FUNCTION update_document_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_updated ON documents;
CREATE TRIGGER trg_documents_updated
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_timestamp();
