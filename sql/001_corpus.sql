-- Curated scholarly corpus
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    author          TEXT,
    death_year      INT,
    manhaj_tag      TEXT,
    reliability_tier SMALLINT NOT NULL CHECK (reliability_tier BETWEEN 1 AND 3),
    collection      TEXT,
    lang            TEXT NOT NULL DEFAULT 'ar',
    license         TEXT,
    source_url      TEXT,
    pending_scholar_review BOOLEAN NOT NULL DEFAULT TRUE,
    pageindex_tree  JSONB,
    review_notes    TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE citations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID REFERENCES documents(id) ON DELETE SET NULL,
    collection      TEXT NOT NULL,
    hadith_ref      TEXT,
    grade           TEXT,
    volume          TEXT,
    page            TEXT,
    url             TEXT,
    cite_key        TEXT NOT NULL UNIQUE,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    citation_id     UUID REFERENCES citations(id) ON DELETE SET NULL,
    text_original   TEXT NOT NULL,
    text_normalized TEXT NOT NULL,
    embedding       vector(1024),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    pageindex_path  TEXT,
    topic_tags      TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE symbols (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical       TEXT NOT NULL UNIQUE,
    aliases         TEXT[] NOT NULL DEFAULT '{}',
    lang            TEXT NOT NULL DEFAULT 'ar',
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE symbol_chunks (
    symbol_id       UUID NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    chunk_id        UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    is_preferred    BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (symbol_id, chunk_id)
);

CREATE INDEX documents_tier_idx ON documents (reliability_tier);
CREATE INDEX documents_author_idx ON documents (author);
CREATE INDEX chunks_document_idx ON chunks (document_id);
CREATE INDEX chunks_metadata_gin ON chunks USING GIN (metadata);
CREATE INDEX chunks_topic_tags_gin ON chunks USING GIN (topic_tags);
CREATE INDEX chunks_pageindex_path_idx ON chunks (pageindex_path);

-- HNSW cosine index (populate after embeddings exist)
CREATE INDEX chunks_embedding_hnsw ON chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
