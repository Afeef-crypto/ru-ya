# Ru-ya documentation

Islamic dream-interpretation assistant: parse a dream into structured parts, retrieve evidence from curated (and optional user) sources, and synthesize **only** from what was retrieved — with citations, disagreement surfacing, and a confidence score.

| Doc | Contents |
|-----|----------|
| [VISION.md](VISION.md) | Product idea, source tiers, authority model |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram, tech stack, component boundaries |
| [INTAKE.md](INTAKE.md) | Pre-dream questionnaire, follow-up slots, UX flow |
| [SCHEMA.md](SCHEMA.md) | Data model rationale (corpus, user sources, sessions) |
| [INGEST.md](INGEST.md) | Curated + user-source ingestion pipeline |
| [RETRIEVER.md](RETRIEVER.md) | Hybrid PageIndex + pgvector retrieval, verify, confidence |
| [GUARDRAILS.md](GUARDRAILS.md) | Refusals, sensitive cases, cite-or-abstain |
| [API.md](API.md) | FastAPI + UI contracts |
| [ROADMAP.md](ROADMAP.md) | Phased build (weeks 1–8) |
| [SOURCES.md](SOURCES.md) | Source inventory + pending scholar review checklist |

SQL migrations live in [`../sql/`](../sql/). Application code lives in [`../src/ru_ya/`](../src/ru_ya/) and [`../web/`](../web/).
