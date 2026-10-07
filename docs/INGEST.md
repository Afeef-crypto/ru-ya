# Ingestion

Code: `src/ru_ya/ingest/`.

## Curated pipeline

```
acquire → clean → normalize → unitize → [PageIndex if long] → embed → upsert → review gate
```

1. **Acquire** — Shamela / OpenITI-style / Sunnah.com exports / licensed PDFs into `data/raw/`.
2. **Clean** — strip boilerplate, fix encoding, preserve structure markers.
3. **Normalize** — `normalize_arabic()` for search/embed; keep original.
4. **Unitize** — logical chunks (hadith+takhrij, commentary section, dictionary entry).
5. **PageIndex** — if page count ≥ 40 (or work is known long commentary), build tree; map leaf nodes ↔ chunk rows via `pageindex_path`.
6. **Embed** — `bge-m3` on normalized text → `vector(1024)`.
7. **Metadata** — tier, author, grade, topic (`ta'bir`, `adab`, `symbol`, `fatwa`).
8. **Review gate** — `pending_scholar_review=true` until human sign-off; blocks tier elevation.

## User pipeline

```
upload → validate → store object → extract text → chunk → [PageIndex if long] → embed → user_chunks ready
```

1. Upload PDF/TXT via `POST /user-sources` → object store.
2. Size / MIME checks (v1: no full AV; document the gap).
3. Extract text; queue OCR if extractable text is too short for page count.
4. Chunk; PageIndex when `page_count >= 40`.
5. Embed into `user_chunks` only.
6. Session retrieval merges curated + owner’s ready user chunks with provenance labels.

### Authority rule

User sources may illustrate or personalize. They **cannot** outrank tier-1 taxonomy hadith on *ru'ya* / *hulm* / *hadith al-nafs* classification. UI always badges them as user-provided.

## Modules

| Module | Role |
|--------|------|
| `normalize.py` | Arabic normalization |
| `chunk.py` | Logical unit chunking |
| `embed.py` | Embedding client (stub + interface) |
| `pageindex_build.py` | Tree build / load interface |
| `curated.py` | Curated upsert helpers |
| `user_upload.py` | User document processing |

## Local seed

`data/seed/` holds fixture texts for development without the full corpus. See `src/ru_ya/ingest/seed_fixture.py`.
