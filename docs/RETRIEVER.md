# Hybrid retriever, verification & confidence

Code: `src/ru_ya/retrieve/`, `src/ru_ya/verify/`.

## Flow

```
DreamGraph + accumulated_facts
        │
        ▼
 per-element queries (symbols, actions, setting, taxonomy)
        │
   ┌────┴────┐
   ▼         ▼
pgvector   PageIndex tree-nav
(HNSW)     (long works)
   │         │
   └────┬────┘
        ▼
 merge / dedupe / rank
        ▼
 CrossSourceVerifier → EvidenceMatrix
        ▼
 ConfidenceScorer
        ▼
 ConclusionSynthesizer (cite-or-abstain)
```

## pgvector path

- Embed normalized query per symbol / scenario / adab question.
- Filters: `reliability_tier`, `author`, `topic`, `lang`; optionally `pending_scholar_review`.
- Include `user_chunks` for session owner.
- Top-k via HNSW cosine distance.

## PageIndex path

- For nominated long works (e.g. *Fath al-Bari*), LLM navigates tree (title + summary) → node IDs.
- Resolve nodes to `chunks` via `pageindex_path`.
- Especially useful for “what do other sources say about this narration” cross-references inside commentary.

## Merge score

```
score = α·semantic + β·tier_boost + γ·pageindex_confidence + δ·user_pref
```

Defaults (tunable): `α=0.45`, `β=0.30`, `γ=0.15`, `δ=0.10`.

Rules:

- Never drop a higher-tier **disagreement** merely because lower-tier sources agree.
- User `preferred_overlay` raises `δ` but still cannot beat tier-1 taxonomy on classification claims.

## Cross-source verification

1. Cluster hits by claim key (e.g. `symbol:snake → enemy`).
2. Label each cluster: `agree` | `qualify` | `disagree`.
3. Check **timeline / place / detail** against `accumulated_facts`:
   - If a source conditions an interpretation on daytime and the dream is night → down-rank application; record in matrix.
4. Emit `EvidenceMatrix` for the synthesizer.

## Confidence (0–100)

Weighted breakdown:

| Component | Weight | Signal |
|-----------|--------|--------|
| `evidence_coverage` | 0.30 | Key symbols/actions found in retrieval |
| `source_agreement` | 0.25 | Share of agree vs disagree clusters |
| `fact_completeness` | 0.20 | Questionnaire + follow-ups vs unknown_slots |
| `tier_quality` | 0.15 | Share of tier 1–2 vs tier 3 / user-only |
| `sensitivity_penalty` | 0.10 | Sacred / distress cases lower the ceiling |

If `evidence_coverage ≈ 0` → abstain (confidence forced low; no improvised conclusion body).

## Example end-to-end (fixture)

See `tests/fixtures/dream_snake_night.json` and `src/ru_ya/retrieve/demo_fixture.py`.
