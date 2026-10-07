# Architecture

## System overview

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js UI (AR/EN, RTL)                                    │
│  IntakeForm · FollowUpTurns · ConclusionView · Upload       │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP + SSE
┌───────────────────────────▼─────────────────────────────────┐
│  FastAPI                                                    │
│  SessionOrchestrator (explicit state machine)               │
│  DreamParser · Guardrails · HybridRetriever                 │
│  CrossSourceVerifier · ConclusionSynthesizer · Ingest API   │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
   ┌────▼────┐      ┌─────▼─────┐    ┌──────▼──────┐
   │Postgres │      │   Redis   │    │ Object store│
   │+pgvector│      │ sessions  │    │ (MinIO/S3)  │
   └────┬────┘      └───────────┘    └──────┬──────┘
        │                                    │
   PageIndex trees (JSON sidecar / DB jsonb) │
```

## Tech stack

| Layer | Choice |
|-------|--------|
| UI | Next.js 15 App Router, RTL-ready, AR/EN |
| API | FastAPI, Pydantic v2, SSE for long runs |
| Orchestration | Explicit state machine — not a free agent loop |
| DB | PostgreSQL 16 + pgvector (HNSW, 1024-d for bge-m3) |
| Cache | Redis (hot session + TTL) |
| Files | S3-compatible (MinIO locally) |
| Embeddings | `BAAI/bge-m3` on Arabic-normalized text |
| LLM | OpenAI-compatible chat API (env-configured) |
| Long documents | PageIndex tree build + LLM tree navigation |
| Short / symbol search | pgvector + metadata filters |
| Workers | RQ (Redis queue) for ingest / OCR / embed |
| Observability | Structured logs + `request_id`; no dream body by default |

## Component boundaries

| Package | Responsibility |
|---------|----------------|
| `ru_ya.api` | HTTP routes, SSE, auth stub, request validation |
| `ru_ya.orchestrator` | Session states, slot merge, when to ask / retrieve / conclude |
| `ru_ya.parser` | DreamGraph extraction + missing-slot detection |
| `ru_ya.guardrails` | Hard refusals and sensitive-case routing |
| `ru_ya.retrieve` | pgvector + PageIndex + merge/rank |
| `ru_ya.verify` | Evidence matrix, timeline/place/detail checks, confidence |
| `ru_ya.synthesize` | Cite-or-abstain conclusion drafting |
| `ru_ya.ingest` | Normalize, chunk, embed, PageIndex build, user uploads |

## Languages

- Corpus: Arabic-first.
- UI: bilingual AR/EN.
- Interpretation language: matches dream language unless the user overrides.

## Dual corpus

1. **Curated** — admin-ingested scholarly library (global `documents` / `chunks`).
2. **User** — private PDF/TXT uploads (`user_documents` / `user_chunks`). Never written into the global index. Labeled “user-provided” in the UI.

## Orchestrator states

```
created → questionnaire_complete → dream_submitted
  → awaiting_followups (≤3 rounds) → ready_to_conclude
  → retrieving → verifying → drafting → concluded
  │
  └─→ refused (guardrail) | expired | purged
```

See [INTAKE.md](INTAKE.md) for UX and [API.md](API.md) for route mapping.
