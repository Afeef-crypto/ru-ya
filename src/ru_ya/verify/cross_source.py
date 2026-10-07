from __future__ import annotations

from typing import Any

from ru_ya.models.dream import DreamGraph
from ru_ya.models.retrieval import EvidenceCluster, EvidenceMatrix, MergedHit, RetrievalResult


def build_evidence_matrix(
    retrieval: RetrievalResult,
    graph: DreamGraph,
    accumulated_facts: dict[str, Any] | None = None,
) -> EvidenceMatrix:
    facts = accumulated_facts or {}
    clusters: list[EvidenceCluster] = []
    used: set[str] = set()

    # Taxonomy / adab cluster
    adab_hits = [
        h
        for h in retrieval.hits
        if "adab" in (h.metadata.get("topic_tags") or [])
        or "taxonomy" in (h.metadata.get("topic_tags") or [])
        or "حلم" in h.text_original
        or "رؤيا" in h.text_original
        or "dream" in h.text_original.lower()
    ]
    if adab_hits:
        clusters.append(
            EvidenceCluster(
                claim_key="taxonomy:ruya_hulm_nafs_adab",
                relation="agree",
                hit_ids=[h.chunk_id for h in adab_hits],
                notes="Adab / classification taxonomy evidence",
            )
        )
        used.update(h.chunk_id for h in adab_hits)

    for symbol in graph.symbols:
        symbol_hits = [
            h
            for h in retrieval.hits
            if symbol.lower() in h.text_original.lower()
            or symbol in (h.metadata.get("topic_tags") or [])
            or symbol in (h.query or "")
        ]
        if not symbol_hits:
            continue
        relation = _relation_for_symbol_hits(symbol_hits)
        timeline_ok, place_ok, detail_ok, downranked, note = _consistency_checks(
            graph, facts, symbol_hits
        )
        clusters.append(
            EvidenceCluster(
                claim_key=f"symbol:{symbol}",
                relation=relation,
                hit_ids=[h.chunk_id for h in symbol_hits],
                notes=note,
                timeline_ok=timeline_ok,
                place_ok=place_ok,
                detail_ok=detail_ok,
                downranked=downranked,
            )
        )
        used.update(h.chunk_id for h in symbol_hits)

    unused = [h.chunk_id for h in retrieval.hits if h.chunk_id not in used]
    return EvidenceMatrix(clusters=clusters, unused_hit_ids=unused)


def _relation_for_symbol_hits(hits: list[MergedHit]) -> str:
    tiers = {h.reliability_tier for h in hits if h.reliability_tier is not None}
    authors = {h.author for h in hits if h.author}
    if len(tiers) > 1 or len(authors) > 1:
        # Multiple tiers/authors without contradiction detection → qualify
        if any(h.reliability_tier == 3 for h in hits) and any(
            h.reliability_tier == 1 for h in hits
        ):
            return "qualify"
        return "agree" if len(authors) <= 1 else "qualify"
    return "agree"


def _consistency_checks(
    graph: DreamGraph,
    facts: dict[str, Any],
    hits: list[MergedHit],
) -> tuple[bool, bool, bool, bool, str | None]:
    timeline_ok = True
    place_ok = True
    detail_ok = True
    downranked = False
    notes: list[str] = []

    day_night = graph.setting.day_night or (facts.get("follow_up_answers") or {}).get(
        "setting_day_night"
    )
    for hit in hits:
        text = hit.text_original.lower()
        # Example condition: if source stresses daytime and dream is night
        if day_night == "night" and ("نهار" in hit.text_original or "daytime" in text):
            timeline_ok = False
            downranked = True
            notes.append("Source condition (day) conflicts with dream night setting")
        if (
            graph.setting.indoor_outdoor == "indoors"
            and ("برية" in hit.text_original or "open desert" in text)
        ):
            place_ok = False
            downranked = True
            notes.append("Place condition may not match indoor setting")

    unknown = facts.get("unknown_slots") or graph.missing_slots
    if unknown:
        detail_ok = False
        notes.append(f"Incomplete slots: {', '.join(unknown)}")

    return timeline_ok, place_ok, detail_ok, downranked, "; ".join(notes) or None
