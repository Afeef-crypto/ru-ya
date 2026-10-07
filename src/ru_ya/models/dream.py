from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

DreamerState = Literal[
    "wudu", "grief", "illness", "anxiety", "pregnancy", "neutral", "other"
]
DreamTime = Literal[
    "last_third_night", "after_fajr", "nap", "other_night", "unknown"
]
Repetition = Literal["once", "recurring", "same_theme"]
WakingEmotion = Literal[
    "fear", "joy", "confusion", "calm", "distress", "other"
]
SensitiveFlag = Literal[
    "prophet", "death", "blood", "sexual", "distress", "none"
]


class Questionnaire(BaseModel):
    dreamer_state: DreamerState
    dream_time: DreamTime
    repetition: Repetition
    waking_emotion: WakingEmotion
    locale_context: str | None = None
    sensitive_flags: list[SensitiveFlag] = Field(default_factory=lambda: ["none"])

    @field_validator("sensitive_flags")
    @classmethod
    def normalize_flags(cls, value: list[SensitiveFlag]) -> list[SensitiveFlag]:
        if not value:
            return ["none"]
        if "none" in value and len(value) > 1:
            raise ValueError("'none' cannot be combined with other sensitive flags")
        return value


class PersonNode(BaseModel):
    label: str
    known: bool | None = None
    relation: str | None = None


class SettingNode(BaseModel):
    indoor_outdoor: str | None = None
    day_night: str | None = None
    place_detail: str | None = None


class DreamGraph(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    people: list[PersonNode] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    emotions: list[str] = Field(default_factory=list)
    setting: SettingNode = Field(default_factory=SettingNode)
    dialogue: list[str] = Field(default_factory=list)
    sequence: list[str] = Field(default_factory=list)
    dreamer_context: dict[str, Any] = Field(default_factory=dict)
    sensitivity_flags: list[str] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    language: str = "ar"


class FollowUpQuestion(BaseModel):
    slot: str
    prompt_en: str
    prompt_ar: str


class DreamSubmit(BaseModel):
    narrative: str = Field(min_length=1)


class FollowUpAnswers(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
