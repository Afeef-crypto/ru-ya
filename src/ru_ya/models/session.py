from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionState(str, Enum):
    CREATED = "created"
    QUESTIONNAIRE_COMPLETE = "questionnaire_complete"
    DREAM_SUBMITTED = "dream_submitted"
    AWAITING_FOLLOWUPS = "awaiting_followups"
    READY_TO_CONCLUDE = "ready_to_conclude"
    RETRIEVING = "retrieving"
    VERIFYING = "verifying"
    DRAFTING = "drafting"
    CONCLUDED = "concluded"
    REFUSED = "refused"
    EXPIRED = "expired"
    PURGED = "purged"


class SessionCreate(BaseModel):
    language: str = Field(default="ar", pattern="^(ar|en)$")
    retain: bool = False
    owner_user_id: str | None = None


class SessionSnapshot(BaseModel):
    id: UUID
    state: SessionState
    language: str
    questionnaire: dict[str, Any] = Field(default_factory=dict)
    accumulated_facts: dict[str, Any] = Field(default_factory=dict)
    follow_up_round: int = 0
    max_follow_up_rounds: int = 3
    retain: bool = False
    expires_at: datetime | None = None
    guardrail_flags: list[str] = Field(default_factory=list)
    pending_follow_ups: list[dict[str, Any]] = Field(default_factory=list)
