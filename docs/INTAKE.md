# Intake UX

## Flow

1. **Create session** — language preference, privacy (`retain` default false).
2. **Pre-dream questionnaire** — required slots must be complete before the dream text box unlocks.
3. **Dream narrative** — free text (AR or EN).
4. **Parse + gap detect** — build `DreamGraph` and `missing_slots`.
5. **Follow-ups** — up to 3 rounds of slot-driven questions; answers merge into `accumulated_facts`.
6. **Conclude** — classify → retrieve → verify → synthesize → render.

Progressive form: do not dump every field on one screen.

## Pre-dream questionnaire slots

| Slot key | Required | Values / notes |
|----------|----------|----------------|
| `dreamer_state` | yes | e.g. `wudu`, `grief`, `illness`, `anxiety`, `pregnancy`, `neutral`, `other` |
| `dream_time` | yes | `last_third_night`, `after_fajr`, `nap`, `other_night`, `unknown` |
| `repetition` | yes | `once`, `recurring`, `same_theme` |
| `waking_emotion` | yes | `fear`, `joy`, `confusion`, `calm`, `distress`, `other` |
| `locale_context` | no | Free text — culture / life context; never used as fatwa |
| `sensitive_flags` | yes (array) | `prophet`, `death`, `blood`, `sexual`, `distress`, `none` |

Validation: if `sensitive_flags` is empty, treat as `["none"]`. Multiple flags allowed except `none` cannot combine with others.

## Follow-up slot schema

Follow-ups are generated from **missing or conflicting** dream slots — not open chat.

| Slot key | Example question (EN) |
|----------|----------------------|
| `people_identity` | Who was the person — known or unknown? |
| `setting_indoor_outdoor` | Was the setting indoors or outdoors? |
| `setting_day_night` | Was it day or night in the dream? |
| `sequence_before` | What happened immediately before the key action? |
| `sequence_after` | What happened immediately after? |
| `observer_or_actor` | Did you speak / act, or only observe? |
| `symbol_detail` | Can you describe the [symbol] more precisely? |
| `color_or_state` | What color / condition was [object]? |
| `spoken_words` | Do you remember any spoken words? |

Rules:

- Max **3** follow-up rounds (`MAX_FOLLOWUP_ROUNDS = 3`).
- After the cap, proceed with unknowns marked in `accumulated_facts.unknown_slots`.
- Each answer is merged into structured JSON; chat transcript is secondary.

## Accumulated facts shape

```json
{
  "questionnaire": { "...": "..." },
  "dream_graph": { "symbols": [], "people": [], "actions": [], "emotions": [], "setting": {}, "sequence": [] },
  "follow_up_answers": { "people_identity": "unknown man" },
  "unknown_slots": ["setting_day_night"],
  "language": "ar",
  "sensitivity_flags": ["none"]
}
```

## Conclusion UI requirements

1. Classification (*ru'ya* / *hulm* / *hadith al-nafs*) + adab guidance.
2. Conclusion (possibility language) + confidence 0–100 with breakdown.
3. Agreement / disagreement across sources.
4. Evidence panel: grade + tier + volume/page.
5. Gaps: unknowns and how they limited confidence.
6. Actions: another follow-up (if not capped), upload source, discard session.
