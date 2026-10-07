# Vision

## Core idea

Each dream is:

1. **Parsed** into structured parts (symbols, people, actions, emotions, setting, dreamer context).
2. **Clarified** via required pre-questions and targeted follow-ups until critical slots are filled (or marked unknown).
3. **Grounded** by retrieving evidence from curated scholarly sources (and optional private user uploads).
4. **Verified** across sources for agreement/disagreement and consistency with timeline, place, and detail.
5. **Answered** only from what was retrieved, with a citation on every claim and an explicit confidence score.

If nothing relevant is retrieved, the system **abstains** — it does not improvise.

## Source curation (product moat)

### Taxonomy layer (tier 1 target)

Hadith on *ru'ya* (true dream), *hulm* (from Shaytan), and *hadith al-nafs* (self-talk). Primary collections: **Bukhari** and **Muslim**. Main commentary: Ibn Hajar, *Fath al-Bari*, Kitab al-Ta'bir.

### Scholarly layer (tier 1–2 target)

Ibn al-Qayyim (e.g. *Kitab al-Ruh*), Ibn Taymiyyah’s fatawa, and contemporary fatawa from Ibn Baz, Ibn Uthaymeen and similar manhaj.

### Dictionary layer (tier 3)

Symbol manuals such as *Tafsir al-Ahlam*. Attribution to Ibn Sirin is **disputed** — always tagged as lower tier, never treated as authoritative alone.

### Metadata per document

Author, death year, manhaj tag, hadith grade (when applicable), reliability tier (1–3), volume/page, license.

**Do not self-certify tiers.** A qualified student of knowledge must review the tier list. Until then every curated document has `pending_scholar_review = true`.

## Authority rules

- Interpretation is presented as **scholarly possibility**, not prediction or certainty.
- Every claim maps to citation IDs; empty citation list → claim forbidden.
- Show hadith grade and source tier next to every cited evidence item.
- User-uploaded sources are labeled “user-provided” and cannot outrank tier-1 taxonomy hadith on classification of *ru'ya* / *hulm* / *hadith al-nafs*.

## Privacy

Dreams are personal. Sessions are **ephemeral by default** (`retain = false`, purge after 24h). Opt-in retention only. Default logs must not contain dream body text.
