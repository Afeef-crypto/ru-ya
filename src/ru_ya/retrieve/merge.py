from __future__ import annotations

from ru_ya.models.retrieval import MergedHit

DEFAULT_WEIGHTS = {
    "alpha": 0.45,  # semantic
    "beta": 0.30,  # tier
    "gamma": 0.15,  # pageindex
    "delta": 0.10,  # user pref
}


def tier_boost(tier: int | None) -> float:
    if tier == 1:
        return 1.0
    if tier == 2:
        return 0.7
    if tier == 3:
        return 0.35
    return 0.2


def merge_hits(
    hits: list[MergedHit],
    *,
    weights: dict[str, float] | None = None,
    top_k: int = 12,
) -> list[MergedHit]:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    by_id: dict[str, MergedHit] = {}
    for hit in hits:
        scored = hit.model_copy(
            update={
                "score": (
                    w["alpha"] * hit.semantic
                    + w["beta"] * hit.tier_boost
                    + w["gamma"] * hit.pageindex_confidence
                    + w["delta"] * hit.user_pref
                )
            }
        )
        existing = by_id.get(scored.chunk_id)
        if existing is None or scored.score > existing.score:
            by_id[scored.chunk_id] = scored

    merged = sorted(by_id.values(), key=lambda h: h.score, reverse=True)
    return merged[:top_k]
