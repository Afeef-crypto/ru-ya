-- Private per-user sources (never merged into curated chunks)

CREATE TABLE user_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id   TEXT NOT NULL,
    filename        TEXT NOT NULL,
    object_key      TEXT NOT NULL,
    mime_type       TEXT,
    page_count      INT,
    status          TEXT NOT NULL DEFAULT 'uploaded'
                    CHECK (status IN ('uploaded', 'processing', 'ready', 'failed')),
    authority_preference TEXT NOT NULL DEFAULT 'informational'
                    CHECK (authority_preference IN ('informational', 'preferred_overlay')),
    pageindex_tree  JSONB,
    error_message   TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_document_id UUID NOT NULL REFERENCES user_documents(id) ON DELETE CASCADE,
    owner_user_id   TEXT NOT NULL,
    text_original   TEXT NOT NULL,
    text_normalized TEXT NOT NULL,
    embedding       vector(1024),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    pageindex_path  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX user_documents_owner_idx ON user_documents (owner_user_id);
CREATE INDEX user_documents_status_idx ON user_documents (status);
CREATE INDEX user_chunks_owner_idx ON user_chunks (owner_user_id);
CREATE INDEX user_chunks_document_idx ON user_chunks (user_document_id);
CREATE INDEX user_chunks_embedding_hnsw ON user_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
