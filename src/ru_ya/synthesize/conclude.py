from __future__ import annotations

from typing import Any

from ru_ya.models.conclusion import (
    Claim,
    ClassificationResult,
    ConclusionPayload,
    Disagreement,
    EvidenceItem,
)
from ru_ya.models.dream import DreamGraph
from ru_ya.models.retrieval import EvidenceMatrix, RetrievalResult
from ru_ya.verify.confidence import score_confidence


def synthesize_conclusion(
    *,
    graph: DreamGraph,
    retrieval: RetrievalResult,
    matrix: EvidenceMatrix,
    accumulated_facts: dict[str, Any] | None = None,
    confidence_ceiling: int = 100,
    language: str = "ar",
) -> ConclusionPayload:
    facts = accumulated_facts or {}
    confidence = score_confidence(
        graph=graph,
        retrieval=retrieval,
        matrix=matrix,
        accumulated_facts=facts,
        confidence_ceiling=confidence_ceiling,
    )

    evidence_items = [_to_evidence(h) for h in retrieval.hits]
    classification = _classify(graph, retrieval)
    adab_hit = next(
        (
            h
            for h in retrieval.hits
            if "adab" in (h.metadata.get("topic_tags") or [])
            or "فليبصق" in h.text_original
            or "seek refuge" in h.text_original.lower()
        ),
        retrieval.hits[0] if retrieval.hits else None,
    )

    if confidence.breakdown.evidence_coverage < 0.05 or not retrieval.hits:
        return ConclusionPayload(
            classification=classification,
            conclusion_md=_abstain_text(language),
            claims=[],
            disagreements=[],
            confidence=confidence,
            gaps=list(facts.get("unknown_slots") or graph.missing_slots),
            evidence=evidence_items,
            abstained=True,
            adab=_adab_block(adab_hit, language),
        )

    claims: list[Claim] = []
    disagreements: list[Disagreement] = []
    for cluster in matrix.clusters:
        cites = [
            h.citation_id or h.cite_key or h.chunk_id
            for h in retrieval.hits
            if h.chunk_id in cluster.hit_ids
        ]
        cites = [c for c in cites if c]
        if not cites:
            continue  # cite-or-abstain: skip uncited claims
        text = _claim_text(cluster.claim_key, cluster.relation, cluster.notes, language)
        claims.append(Claim(text=text, citation_ids=cites))
        if cluster.relation in ("disagree", "qualify") or cluster.downranked:
            disagreements.append(
                Disagreement(
                    claim_key=cluster.claim_key,
                    summary=cluster.notes
                    or "Sources qualify or condition this interpretation.",
                    citation_ids=cites,
                )
            )

    conclusion_md = _draft_markdown(
        language=language,
        classification=classification,
        claims=claims,
        disagreements=disagreements,
        confidence_score=confidence.score,
        graph=graph,
    )
    conclusion_md = _maybe_llm_polish(
        language=language,
        draft_md=conclusion_md,
        claims=claims,
        evidence_items=evidence_items,
        classification=classification,
        graph=graph,
        facts=facts,
    )

    return ConclusionPayload(
        classification=classification,
        conclusion_md=conclusion_md,
        claims=claims,
        disagreements=disagreements,
        confidence=confidence,
        gaps=list(facts.get("unknown_slots") or graph.missing_slots),
        evidence=evidence_items,
        abstained=False,
        adab=_adab_block(adab_hit, language),
    )


def _to_evidence(hit) -> EvidenceItem:
    return EvidenceItem(
        citation_id=hit.citation_id,
        cite_key=hit.cite_key,
        excerpt=hit.text_original[:500],
        reliability_tier=hit.reliability_tier,
        hadith_grade=hit.hadith_grade,
        author=hit.author,
        source_scope=hit.source_scope,
        pending_scholar_review=hit.pending_scholar_review,
        volume=(hit.metadata or {}).get("volume"),
        page=(hit.metadata or {}).get("page"),
    )


def _classify(graph: DreamGraph, retrieval: RetrievalResult) -> ClassificationResult:
    emotion = (graph.dreamer_context or {}).get("waking_emotion")
    # Soft heuristic pending LLM + retrieved taxonomy weighting
    if emotion in ("fear", "distress") or "hulm" in " ".join(
        h.text_original.lower() for h in retrieval.hits
    ):
        return ClassificationResult(ruya=0.15, hulm=0.55, hadith_al_nafs=0.30, label="hulm")
    if (graph.dreamer_context or {}).get("dream_time") == "last_third_night":
        return ClassificationResult(ruya=0.45, hulm=0.20, hadith_al_nafs=0.35, label="uncertain")
    return ClassificationResult(ruya=0.25, hulm=0.25, hadith_al_nafs=0.50, label="hadith_al_nafs")


def _adab_block(hit, language: str) -> dict[str, Any]:
    if hit is None:
        return {"text": "", "citation_ids": []}
    if language == "ar":
        text = (
            "إن كانت الرؤيا مما يُسرّ فليحمد الله، وإن كانت مما يكره "
            "فليتعوذ بالله وليبصق عن يساره ثلاثاً ولا يحدّث بها على وجه يضر — حسب ما ورد في النصوص المسترجعة."
        )
    else:
        text = (
            "For a pleasing dream, give thanks to Allah. For a disliked dream, "
            "seek refuge with Allah, spit lightly to the left three times, and do not narrate it "
            "in a harmful way — per the retrieved narrations."
        )
    return {
        "text": text,
        "citation_ids": [hit.citation_id or hit.cite_key or hit.chunk_id],
    }


def _claim_text(claim_key: str, relation: str, notes: str | None, language: str) -> str:
    if claim_key.startswith("symbol:"):
        symbol = claim_key.split(":", 1)[1]
        if language == "ar":
            base = f"قد يُفهم رمز «{symbol}» في ضوء المصادر المسترجعة كإمكانية تفسيرية"
        else:
            base = f"The symbol «{symbol}» may be read, per retrieved sources, as a scholarly possibility"
        if relation != "agree":
            base += (
                " — مع اختلاف أو تقييد بين المصادر"
                if language == "ar"
                else " — with qualification or disagreement among sources"
            )
        if notes:
            base += f" ({notes})"
        return base + "."
    if language == "ar":
        return "تشير النصوص المسترجعة إلى التفريق بين الرؤيا والحلم وحديث النفس مع أدب التعامل مع المنام."
    return (
        "Retrieved texts distinguish ru'ya, hulm, and hadith al-nafs, and include adab for dreams."
    )


def _draft_markdown(
    *,
    language: str,
    classification: ClassificationResult,
    claims: list[Claim],
    disagreements: list[Disagreement],
    confidence_score: int,
    graph: DreamGraph,
) -> str:
    if language == "ar":
        lines = [
            f"## خلاصة أولية (إمكانية علمية — ليست قطعاً)",
            f"**التصنيف المقترح:** `{classification.label}` (ثقة إجمالية {confidence_score}/100).",
            "",
            "### ما يمكن قوله بناءً على الأدلة المسترجعة",
        ]
        for c in claims:
            lines.append(f"- {c.text} 〔{', '.join(c.citation_ids)}〕")
        if disagreements:
            lines.extend(["", "### مواضع الخلاف أو التقييد"])
            for d in disagreements:
                lines.append(f"- {d.claim_key}: {d.summary}")
        if _active_sensitivity(graph):
            lines.extend(
                [
                    "",
                    "### تنبيه",
                    "هذه الحالة تتطلب صياغة حذرة نظراً لحساسيتها.",
                ]
            )
        return "\n".join(lines)

    lines = [
        "## Preliminary conclusion (scholarly possibility — not certainty)",
        f"**Suggested classification:** `{classification.label}` (overall confidence {confidence_score}/100).",
        "",
        "### What can be said from retrieved evidence",
    ]
    for c in claims:
        lines.append(f"- {c.text} [{', '.join(c.citation_ids)}]")
    if disagreements:
        lines.extend(["", "### Disagreement / qualification"])
        for d in disagreements:
            lines.append(f"- {d.claim_key}: {d.summary}")
    if _active_sensitivity(graph):
        lines.extend(
            [
                "",
                "### Caution",
                "This case requires careful wording due to sensitivity flags.",
            ]
        )
    return "\n".join(lines)


def _active_sensitivity(graph: DreamGraph) -> list[str]:
    return [f for f in (graph.sensitivity_flags or []) if f and f != "none"]


def _maybe_llm_polish(
    *,
    language: str,
    draft_md: str,
    claims: list[Claim],
    evidence_items: list[EvidenceItem],
    classification: ClassificationResult,
    graph: DreamGraph,
    facts: dict[str, Any],
) -> str:
    try:
        from ru_ya.llm.client import get_llm_client

        client = get_llm_client()
        if not client.enabled:
            return draft_md
    except Exception:  # noqa: BLE001
        return draft_md

    evidence_brief = "\n".join(
        f"- [{e.cite_key or e.citation_id}] tier={e.reliability_tier} grade={e.hadith_grade}: {e.excerpt[:280]}"
        for e in evidence_items[:8]
    )
    claims_brief = "\n".join(
        f"- {c.text} cites={','.join(c.citation_ids)}" for c in claims
    )
    system = (
        "You are Ru-ya, a careful Islamic dream-interpretation assistant. "
        "Rewrite the draft conclusion. Rules: scholarly possibility only (not certainty); "
        "every substantive claim must keep its citation ids; do not invent sources or rulings; "
        "no medical/fiqh/life-decision directives; surface disagreement if present; "
        "keep adab framing. Output markdown only."
    )
    user = (
        f"Language: {language}\n"
        f"Classification: {classification.label}\n"
        f"Dream graph: {graph.model_dump()}\n"
        f"Facts: {facts}\n"
        f"Claims:\n{claims_brief}\n"
        f"Evidence:\n{evidence_brief}\n"
        f"Draft:\n{draft_md}\n"
    )
    try:
        polished = client.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=900,
        ).strip()
        return polished or draft_md
    except Exception:  # noqa: BLE001
        return draft_md


def _abstain_text(language: str) -> str:
    if language == "ar":
        return (
            "لم يُسترجع من المصادر ما يكفي لصياغة تفسير معزو. "
            "لا نختلق معنى خارج الأدلة. يمكنك إضافة تفاصيل أو رفع مصدر خاص بالجلسة."
        )
    return (
        "Insufficient evidence was retrieved to draft a cited interpretation. "
        "Ru-ya will not invent meanings. You may add details or upload a private source."
    )
