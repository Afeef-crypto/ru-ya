# Source inventory & scholar review

**Status:** `pending_scholar_review = true` for all rows until a qualified student of knowledge signs off. Do not treat the provisional tiers below as certified.

## Provisional tier guide (for reviewers)

| Tier | Meaning | Examples (provisional) |
|------|---------|------------------------|
| 1 | Primary taxonomy / sahih foundation | Bukhari & Muslim chapters on dreams; *Fath al-Bari* Kitab al-Ta'bir as commentary on those |
| 2 | Strong scholarly discussion | Ibn al-Qayyim (*Kitab al-Ruh* sections on dreams), Ibn Taymiyyah, Ibn Baz, Ibn Uthaymeen fatawa on dreams |
| 3 | Secondary / disputed attribution / popular manuals | *Tafsir al-Ahlam* (Ibn Sirin attribution disputed) and similar dictionaries |

## Seed acquisition targets

| Work | Layer | Format target | Notes |
|------|-------|---------------|-------|
| Sahih al-Bukhari — Kitab al-Ta'bir | Taxonomy | Structured hadith + takhrij | Prefer graded editions / Sunnah.com refs |
| Sahih Muslim — related chapters | Taxonomy | Structured hadith + takhrij | Cross-link parallel narrations |
| Ibn Hajar — *Fath al-Bari* (Kitab al-Ta'bir) | Commentary | Long PDF/text → PageIndex | Tree nav preferred over flat chunks alone |
| Ibn al-Qayyim — *Kitab al-Ruh* (dream sections) | Scholarly | Cleaned text | Slice relevant sections only |
| Selected fatawa (Ibn Baz, Ibn Uthaymeen) | Scholarly | Short units | Topic-tag `fatwa`, `adab`, `ta'bir` |
| *Tafsir al-Ahlam* | Dictionary | One entry = one chunk | Cap tier 3; flag disputed attribution |

## Reviewer checklist

- [ ] Confirm or revise tier for each document in the seed set  
- [ ] Confirm hadith grades shown in UI match an agreed reference edition  
- [ ] Approve manhaj tags and authorship metadata  
- [ ] Confirm *Tafsir al-Ahlam* remains ≤ tier 3  
- [ ] Sign off: name, date, notes → store in `documents.review_notes` / review log  

Until checklist is complete, the API may still retrieve seed content but UI must show **“pending scholar review”** on tier badges when `pending_scholar_review` is true.
