from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MergedHit(BaseModel):
    chunk_id: str
    source_scope: Literal["curated", "user"]
    text_original: str
    score: float
    semantic: float = 0.0
    tier_boost: float = 0.0
    pageindex_confidence: float = 0.0
    user_pref: float = 0.0
    reliability_tier: int | None = None
    author: str | None = None
    citation_id: str | None = None
    cite_key: str | None = None
    hadith_grade: str | None = None
    pending_scholar_review: bool = True
    pageindex_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    query: str | None = None


class RetrievalResult(BaseModel):
    queries: list[str] = Field(default_factory=list)
    hits: list[MergedHit] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)


ClaimRelation = Literal["agree", "qualify", "disagree"]


class EvidenceCluster(BaseModel):
    claim_key: str
    relation: ClaimRelation
    hit_ids: list[str] = Field(default_factory=list)
    notes: str | None = None
    timeline_ok: bool = True
    place_ok: bool = True
    detail_ok: bool = True
    downranked: bool = False


class EvidenceMatrix(BaseModel):
    clusters: list[EvidenceCluster] = Field(default_factory=list)
    unused_hit_ids: list[str] = Field(default_factory=list)
