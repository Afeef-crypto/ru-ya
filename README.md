# Ru-ya

Cite-or-abstain Islamic dream interpretation assistant: structured intake → hybrid retrieval (pgvector + PageIndex) → cross-source verification → confidence-scored conclusion with citations.

Dreams are **not retained by default** (24h purge). Interpretation is scholarly possibility, not prophecy. Source tiers stay `pending_scholar_review` until a qualified student of knowledge signs off.

## Docs

See [docs/README.md](docs/README.md) for architecture, intake UX, schema, ingest, retriever, guardrails, API, and roadmap.

## Repo layout

```
docs/           Architecture & product specs
sql/            Postgres + pgvector migrations
src/ru_ya/      FastAPI + orchestrator + RAG modules
web/            Next.js intake UI (skeleton)
tests/          Unit + end-to-end fixture
```

## Quick start (API)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn ru_ya.api.main:app --reload --app-dir src
```

Health: `GET http://localhost:8000/health`

## Quick start (UI)

```bash
cd web
npm install
set NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
npm run dev
```

## Fixture dream (offline)

```bash
python -m ru_ya.retrieve.demo_fixture
# or
pytest -q
```

## Stack (locked)

Next.js · FastAPI · PostgreSQL 16 + pgvector · Redis · bge-m3 · PageIndex · OpenRouter (OpenAI-compatible) LLM (wired later; skeleton uses deterministic local stubs).
