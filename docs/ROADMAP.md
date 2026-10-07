# Roadmap

## Phase A — Foundations (Week 1)

- Architecture docs in `docs/`
- SQL migrations + Pydantic schemas
- Source inventory + tier table marked pending review
- Slot schema for questionnaire + follow-ups
- FastAPI session skeleton + stub retrieve/conclude

## Phase B — Ingest MVP (Weeks 2–3)

- Seed curated set (Bukhari/Muslim ta'bir hadiths, sample *Fath al-Bari* sections, sample dictionary entries)
- Arabic normalizer, chunker, embedder, HNSW index
- PageIndex tree for one long book
- User upload: TXT first, then PDF

## Phase C — Session orchestrator (Weeks 3–4)

- Full pre-questions → dream → follow-up → accumulated_facts
- Guardrail classifier
- Hybrid retriever merge
- Cross-source verifier + confidence scorer
- Cite-or-abstain synthesizer with real LLM wiring

## Phase D — UI (Weeks 5–6)

- Intake form, follow-up UI, conclusion + evidence drawer
- User source upload
- AR/EN + RTL
- Privacy controls (discard / don’t retain)

## Phase E — Eval & harden (Weeks 6–8)

- Golden set ~50 dreams (scholar-reviewed)
- Metrics: citation faithfulness, tier-correct retrieval, refusal correctness, confidence calibration
- Purge jobs, rate limits, production compose

## Explicit non-goals (v1)

- Self-certified scholarly tiers
- Autonomous fatwa or medical advice
- Public dream sharing
- Training custom LLMs
