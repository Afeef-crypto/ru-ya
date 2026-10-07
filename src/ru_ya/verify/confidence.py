from __future__ import annotations

from typing import Any

from ru_ya.models.conclusion import Confidence, ConfidenceBreakdown
from ru_ya.models.dream import DreamGraph
from ru_ya.models.retrieval import EvidenceMatrix, RetrievalResult

WEIGHTS = {
    "evidence_coverage": 0.30,
    "source_agreement": 0.25,
    "fact_completeness": 0.20,
    "tier_quality": 0.15,
    "sensitivity_penalty": 0.10,
}


def score_confidence(
    *,
    graph: DreamGraph,
    retrieval: RetrievalResult,
    matrix: EvidenceMatrix,
    accumulated_facts: dict[str, Any] | None = None,
    confidence_ceiling: int = 100,
) -> Confidence:
    facts = accumulated_facts or {}
    coverage = _evidence_coverage(graph, retrieval)
    agreement = _source_agreement(matrix)
    completeness = _fact_completeness(graph, facts)
    tier_q = _tier_quality(retrieval)
    sensit = _sensitivity_penalty(graph)

    breakdown = ConfidenceBreakdown(
        evidence_coverage=coverage,
        source_agreement=agreement,
        fact_completeness=completeness,
        tier_quality=tier_q,
        sensitivity_penalty=sensit,
    )

    raw = (
        WEIGHTS["evidence_coverage"] * coverage
        + WEIGHTS["source_agreement"] * agreement
        + WEIGHTS["fact_completeness"] * completeness
        + WEIGHTS["tier_quality"] * tier_q
        + WEIGHTS["sensitivity_penalty"] * (1.0 - sensit)
    )
    score = int(round(max(0.0, min(1.0, raw)) * 100))
    if coverage < 0.05:
        score = min(score, 15)
    score = min(score, confidence_ceiling)
    return Confidence(score=score, breakdown=breakdown)


def _evidence_coverage(graph: DreamGraph, retrieval: RetrievalResult) -> float:
    keys = list(graph.symbols) + list(graph.actions[:3])
    if not keys:
        return 0.4 if retrieval.hits else 0.0
    found = 0
    blob = " ".join(h.text_original.lower() for h in retrieval.hits)
    for key in keys:
        if key.lower() in blob or any(key in (h.query or "") for h in retrieval.hits):
            found += 1
    return found / len(keys)


def _source_agreement(matrix: EvidenceMatrix) -> float:
    if not matrix.clusters:
        return 0.0
    score = 0.0
    for c in matrix.clusters:
        if c.relation == "agree" and not c.downranked:
            score += 1.0
        elif c.relation == "qualify" or c.downranked:
            score += 0.55
        else:
            score += 0.25
    return score / len(matrix.clusters)


def _fact_completeness(graph: DreamGraph, facts: dict[str, Any]) -> float:
    unknown = list(facts.get("unknown_slots") or graph.missing_slots or [])
    # 4 critical slots baseline
    return max(0.0, 1.0 - (len(unknown) / 4.0))


def _tier_quality(retrieval: RetrievalResult) -> float:
    if not retrieval.hits:
        return 0.0
    weights = []
    for h in retrieval.hits:
        if h.source_scope == "user":
            weights.append(0.25)
        elif h.reliability_tier == 1:
            weights.append(1.0)
        elif h.reliability_tier == 2:
            weights.append(0.75)
        else:
            weights.append(0.4)
    return sum(weights) / len(weights)


def _sensitivity_penalty(graph: DreamGraph) -> float:
    flags = set(graph.sensitivity_flags or [])
    penalty = 0.0
    if "prophet" in flags:
        penalty += 0.5
    if "death" in flags:
        penalty += 0.35
    if "distress" in flags:
        penalty += 0.25
    if "blood" in flags or "sexual" in flags:
        penalty += 0.2
    return min(1.0, penalty)
