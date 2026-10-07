from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailDecision:
    allowed: bool = True
    refuse_codes: list[str] = field(default_factory=list)
    sensitive_flags: list[str] = field(default_factory=list)
    message_en: str | None = None
    message_ar: str | None = None
    confidence_ceiling: int = 100


_RULING_PATTERNS = [
    r"\b(fatwa|ruling|haram|halal|must I|should I marry|divorce)\b",
    r"(أفتني|حكم شرعي|حرام|حلال|هل يجب|أتزوج|طلاق)",
]
_HEALTH_PATTERNS = [
    r"\b(diagnos|cancer|disease|medicine|doctor|cure)\b",
    r"(تشخيص|سرطان|مرض|دواء|علاج طبي)",
]
_LIFE_DECISION_PATTERNS = [
    r"\b(quit (my )?job|must travel|sell (my )?house)\b",
    r"(أترك عملي|يجب أن أسافر|أبيع بيتي)",
]


def evaluate_guardrails(
    *,
    narrative: str | None = None,
    questionnaire: dict[str, Any] | None = None,
    accumulated_facts: dict[str, Any] | None = None,
) -> GuardrailDecision:
    q = questionnaire or {}
    facts = accumulated_facts or {}
    text = narrative or ""
    flags = list(q.get("sensitive_flags") or facts.get("sensitivity_flags") or [])
    if "none" in flags and len(flags) > 1:
        flags = [f for f in flags if f != "none"]

    decision = GuardrailDecision(sensitive_flags=[f for f in flags if f != "none"])

    for pat in _RULING_PATTERNS:
        if re.search(pat, text, re.I):
            decision.allowed = False
            decision.refuse_codes.append("refuse_fiqh_ruling")
    for pat in _HEALTH_PATTERNS:
        if re.search(pat, text, re.I):
            decision.allowed = False
            decision.refuse_codes.append("refuse_health")
    for pat in _LIFE_DECISION_PATTERNS:
        if re.search(pat, text, re.I):
            decision.allowed = False
            decision.refuse_codes.append("refuse_life_decision")

    if "prophet" in decision.sensitive_flags:
        decision.confidence_ceiling = min(decision.confidence_ceiling, 55)
    if "death" in decision.sensitive_flags:
        decision.confidence_ceiling = min(decision.confidence_ceiling, 60)
    if "distress" in decision.sensitive_flags:
        decision.confidence_ceiling = min(decision.confidence_ceiling, 70)

    if not decision.allowed:
        decision.message_en = (
            "This request asks for a ruling, health direction, or major life decision "
            "from a dream. Ru-ya will not provide that. You may rephrase to seek "
            "scholarly possibilities with citations, and classical adab for dreams."
        )
        decision.message_ar = (
            "هذا الطلب يطلب حكماً شرعياً أو توجيهاً صحياً أو قراراً مصيرياً بناءً على المنام. "
            "لا يقدّم رُؤيا ذلك. يمكنك إعادة الصياغة لطلب إمكانات علمية معزوة، مع أدب الرؤيا."
        )
    return decision
