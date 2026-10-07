from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    ruya: float = 0.0
    hulm: float = 0.0
    hadith_al_nafs: float = 0.0
    label: Literal["ruya", "hulm", "hadith_al_nafs", "uncertain"] = "uncertain"


class ConfidenceBreakdown(BaseModel):
    evidence_coverage: float = 0.0
    source_agreement: float = 0.0
    fact_completeness: float = 0.0
    tier_quality: float = 0.0
    sensitivity_penalty: float = 0.0


class Confidence(BaseModel):
    score: int = Field(ge=0, le=100)
    breakdown: ConfidenceBreakdown = Field(default_factory=ConfidenceBreakdown)


class Claim(BaseModel):
    text: str
    citation_ids: list[str] = Field(default_factory=list)


class Disagreement(BaseModel):
    claim_key: str
    summary: str
    citation_ids: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    citation_id: str | None = None
    cite_key: str | None = None
    excerpt: str
    reliability_tier: int | None = None
    hadith_grade: str | None = None
    author: str | None = None
    source_scope: Literal["curated", "user"] = "curated"
    pending_scholar_review: bool = True
    volume: str | None = None
    page: str | None = None


class ConclusionPayload(BaseModel):
    classification: ClassificationResult = Field(default_factory=ClassificationResult)
    adab: dict[str, Any] = Field(default_factory=dict)
    conclusion_md: str = ""
    claims: list[Claim] = Field(default_factory=list)
    disagreements: list[Disagreement] = Field(default_factory=list)
    confidence: Confidence = Field(
        default_factory=lambda: Confidence(score=0, breakdown=ConfidenceBreakdown())
    )
    gaps: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    abstained: bool = False
    guardrail_flags: list[str] = Field(default_factory=list)
