# Guardrails

Hard gates run **before** synthesis. Soft framing rules apply to all allowed outputs.

## Hard refusals

Refuse to produce directives that:

- Derive **fiqh rulings** from the dream alone.
- Give **medical / health** advice or diagnosis.
- Push **major life decisions** (“you must marry / quit / travel / divorce”) based on the dream.

Response shape: short refusal reason, offer to continue with scholarly-possibility framing if the user rephrases away from seeking a ruling, and still offer classical **adab** for good/bad dreams when taxonomy evidence exists.

## Framing (always)

- Scholarly **possibility**, not prophecy or certainty.
- Cite-or-abstain: no claim without citation IDs from the current retrieval run.
- Show **hadith grade** and **reliability tier** beside every evidence item.
- Surface disagreement; do not flatten scholars into a fake consensus.

## Sensitive cases

| Flag | Handling |
|------|----------|
| `prophet` | High-tier sources only; careful fixed wording; confidence ceiling lowered; never claim authenticity of the vision unless classical criteria are explicitly met and cited |
| `death` | Careful wording; no predictions of someone’s death; emphasize adab and uncertainty |
| `blood` / `sexual` | Minimize graphic restatement; keep scholarly tone; avoid speculative moral accusations |
| `distress` | Empathetic, non-clinical language; no therapy claims; suggest seeking support in real life without diagnosing |

Sensitive paths may use dedicated prompt templates in `ru_ya.synthesize.sensitive`.

## Adab (always available when evidence exists)

For good dreams: encourage gratitude / hope as per retrieved hadith.  
For bad dreams: seek refuge, spit lightly thrice (left), do not narrate harmfully — **only** as cited from retrieved taxonomy sources.

## Logging

- Log `session_id`, state transitions, guardrail codes, retrieval counts.
- Do **not** log dream narrative or questionnaire free text by default.
