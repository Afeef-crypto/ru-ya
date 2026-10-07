# Schema

PostgreSQL 16 + `pgvector`. UUID primary keys. Embeddings: `vector(1024)` for `bge-m3`. PageIndex trees stored as `jsonb` (and optionally mirrored as files under `data/pageindex/`).

Migrations:

- [`sql/001_corpus.sql`](../sql/001_corpus.sql) — curated library
- [`sql/002_user_sources.sql`](../sql/002_user_sources.sql) — private uploads
- [`sql/003_sessions.sql`](../sql/003_sessions.sql) — sessions, turns, retrieval, conclusions

## Arabic text dual-storage

| Column | Purpose |
|--------|---------|
| `text_original` | Display + citations (diacritics preserved when available) |
| `text_normalized` | Embedding + search (strip diacritics; unify alef / ya / ta-marbuta) |

## Curated corpus

### `documents`

One curated work or edition.

- `author`, `death_year`, `manhaj_tag`, `reliability_tier` (1–3)
- `collection`, `lang`, `license`, `source_url`
- `pending_scholar_review` (default true)
- `pageindex_tree` jsonb (nullable) — tree for long structured books
- `review_notes` text

### `chunks`

Logical units: one hadith + takhrij, one commentary section, or one dictionary entry.

- `document_id`, `text_original`, `text_normalized`, `embedding`
- `metadata` jsonb — topic tags, volume, page, hadith refs, grades
- `pageindex_path` text — node path for join-back to tree
- `citation_id` nullable FK

### `symbols`

Canonical symbol + aliases; optional preferred chunk links via `symbol_chunks`.

### `citations`

Stable cite keys: `collection`, `hadith_ref`, `grade`, `volume`, `page`, `url`, `document_id`.

## User sources

### `user_documents`

Owned by `owner_user_id`. Status: `uploaded` → `processing` → `ready` | `failed`.

- `authority_preference`: `informational` | `preferred_overlay`
- `object_key`, `page_count`, `pageindex_tree`

### `user_chunks`

Same embedding space as curated chunks but scoped by `user_id` / `user_document_id`. Never copied into `chunks`.

## Sessions

### `sessions`

- `language`, `questionnaire` jsonb, `accumulated_facts` jsonb
- `state`, `follow_up_round`, `retain` (default false), `expires_at`
- `owner_user_id` nullable (anonymous sessions allowed in v1)

### `session_turns`

`turn_type`: `pre_q` | `dream` | `follow_up` | `conclusion` | `system`

### `retrieval_runs`

Queries issued, hit chunk IDs (curated + user), scores, filters.

### `conclusions`

Final markdown, classification distribution, confidence breakdown, citation map, disagreement map, guardrail flags.

## Indexes

- HNSW on `chunks.embedding` and `user_chunks.embedding`
- GIN on `chunks.metadata` and session jsonb as needed
- B-tree on `documents.reliability_tier`, `documents.author`, `sessions.expires_at`

## Retention

Purge job deletes sessions where `retain = false` and `expires_at < now()`, cascading turns / retrieval_runs / conclusions. Dream body lives primarily in turns + accumulated_facts.
