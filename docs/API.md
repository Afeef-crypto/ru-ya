# API & UI contracts

## FastAPI routes

Base: `/api/v1`.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/sessions` | Create session |
| PUT | `/sessions/{id}/questionnaire` | Save pre-questions; transition state |
| POST | `/sessions/{id}/dream` | Submit narrative → parse → follow-ups or ready |
| POST | `/sessions/{id}/follow-ups` | Answer follow-ups → re-parse / proceed |
| POST | `/sessions/{id}/conclude` | Retrieve → verify → synthesize (SSE) |
| GET | `/sessions/{id}` | Session snapshot |
| GET | `/sessions/{id}/conclusion` | Final conclusion payload |
| DELETE | `/sessions/{id}` | Purge dream data |
| POST | `/user-sources` | Upload private source (`multipart`) |
| GET | `/user-sources` | List ready sources for user |

### SSE events (`POST .../conclude`)

`parsing` · `asking_followups` · `retrieving` · `verifying` · `drafting` · `done` · `refused` · `error`

## Key payloads

### Create session

```json
{ "language": "ar", "retain": false, "owner_user_id": null }
```

### Questionnaire

See slot keys in [INTAKE.md](INTAKE.md).

### Dream submit response

```json
{
  "session_id": "...",
  "state": "awaiting_followups",
  "follow_up_questions": [
    { "slot": "people_identity", "prompt_en": "...", "prompt_ar": "..." }
  ],
  "dream_graph_preview": {}
}
```

### Conclusion

```json
{
  "classification": { "ruya": 0.2, "hulm": 0.5, "hadith_al_nafs": 0.3, "label": "hulm" },
  "adab": { "text": "...", "citation_ids": ["..."] },
  "conclusion_md": "...",
  "claims": [{ "text": "...", "citation_ids": ["..."] }],
  "disagreements": [],
  "confidence": {
    "score": 62,
    "breakdown": {
      "evidence_coverage": 0.7,
      "source_agreement": 0.5,
      "fact_completeness": 0.8,
      "tier_quality": 0.6,
      "sensitivity_penalty": 0.0
    }
  },
  "gaps": ["setting_day_night"],
  "evidence": []
}
```

## Next.js UI (contracts only in this slice)

App under `web/`:

| Route | Role |
|-------|------|
| `/` | Landing → start session |
| `/session/[id]/intake` | Questionnaire + dream text |
| `/session/[id]/follow-ups` | Follow-up questions |
| `/session/[id]/conclusion` | Result + evidence drawer |
| `/sources` | User source upload / list |

Shared types: `web/lib/api-types.ts` mirrors Pydantic models.

Env: `NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1`.
