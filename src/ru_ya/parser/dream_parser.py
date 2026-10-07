from __future__ import annotations

import re
from typing import Any

from ru_ya.models.dream import DreamGraph, PersonNode, SettingNode
from ru_ya.parser.slots import CRITICAL_SLOTS

# Lightweight keyword cues for the offline skeleton (LLM replaces this later).
_SYMBOL_CUES = {
    "snake": ("snake", "serpent", "حية", "ثعبان"),
    "water": ("water", "river", "sea", "ماء", "نهر", "بحر"),
    "fire": ("fire", "نار"),
    "tree": ("tree", "شجرة"),
    "bird": ("bird", "طائر", "عصفور"),
    "house": ("house", "home", "بيت", "منزل"),
    "prophet": ("prophet", "النبي", "رسول الله"),
}


def parse_dream_narrative(
    narrative: str,
    *,
    questionnaire: dict[str, Any] | None = None,
    prior_facts: dict[str, Any] | None = None,
    language: str = "ar",
) -> DreamGraph:
    text = narrative.strip()
    lower = text.lower()
    q = questionnaire or {}
    prior = prior_facts or {}
    follow_answers = dict(prior.get("follow_up_answers") or {})

    symbols = [name for name, cues in _SYMBOL_CUES.items() if any(c in lower or c in text for c in cues)]
    people = _extract_people(text, follow_answers)
    actions = _extract_actions(text)
    emotions = _extract_emotions(text, q)
    setting = _extract_setting(text, follow_answers)
    sensitivity = list(q.get("sensitive_flags") or prior.get("sensitivity_flags") or [])
    if any(c in lower or c in text for c in _SYMBOL_CUES["prophet"]):
        if "prophet" not in sensitivity:
            sensitivity = [f for f in sensitivity if f != "none"] + ["prophet"]

    missing = _detect_missing_slots(people, setting, follow_answers, symbols)

    return DreamGraph(
        symbols=symbols,
        people=people,
        actions=actions,
        emotions=emotions,
        setting=setting,
        dialogue=_extract_dialogue(text),
        sequence=[s.strip() for s in re.split(r"[.\n؟!]+", text) if s.strip()][:8],
        dreamer_context={
            "dreamer_state": q.get("dreamer_state"),
            "dream_time": q.get("dream_time"),
            "repetition": q.get("repetition"),
            "waking_emotion": q.get("waking_emotion"),
            "locale_context": q.get("locale_context"),
        },
        sensitivity_flags=sensitivity,
        missing_slots=missing,
        language=language,
    )


def _extract_people(text: str, follow_answers: dict[str, str]) -> list[PersonNode]:
    people: list[PersonNode] = []
    if re.search(r"\b(man|woman|person|رجل|امرأة|شخص)\b", text, re.I):
        known = None
        if "people_identity" in follow_answers:
            ans = follow_answers["people_identity"].lower()
            known = "unknown" not in ans and "مجهول" not in ans
        people.append(PersonNode(label="person", known=known))
    elif "people_identity" in follow_answers:
        people.append(
            PersonNode(
                label=follow_answers["people_identity"],
                known="unknown" not in follow_answers["people_identity"].lower(),
            )
        )
    return people


def _extract_actions(text: str) -> list[str]:
    actions = []
    patterns = [
        (r"\b(ran|running|يجري|ركض)\b", "running"),
        (r"\b(ate|eating|يأكل|أكل)\b", "eating"),
        (r"\b(fell|falling|سقط|يقع)\b", "falling"),
        (r"\b(saw|seeing|رأيت|أرى)\b", "seeing"),
        (r"\b(spoke|speaking|قال|تكلم)\b", "speaking"),
    ]
    for pat, label in patterns:
        if re.search(pat, text, re.I):
            actions.append(label)
    return actions


def _extract_emotions(text: str, questionnaire: dict[str, Any]) -> list[str]:
    emotions = []
    if questionnaire.get("waking_emotion"):
        emotions.append(str(questionnaire["waking_emotion"]))
    for pat, label in [
        (r"\b(afraid|fear|خوف|خائف)\b", "fear"),
        (r"\b(happy|joy|فرح|سعيد)\b", "joy"),
        (r"\b(confused|حيران|مرتبك)\b", "confusion"),
    ]:
        if re.search(pat, text, re.I):
            emotions.append(label)
    return list(dict.fromkeys(emotions))


def _extract_setting(text: str, follow_answers: dict[str, str]) -> SettingNode:
    indoor = follow_answers.get("setting_indoor_outdoor")
    day_night = follow_answers.get("setting_day_night")
    if indoor is None:
        if re.search(r"\b(inside|indoors|داخل|بيت|غرفة)\b", text, re.I):
            indoor = "indoors"
        elif re.search(r"\b(outside|outdoors|خارج|شارع|برية)\b", text, re.I):
            indoor = "outdoors"
    if day_night is None:
        if re.search(r"\b(night|ليل|ليلا)\b", text, re.I):
            day_night = "night"
        elif re.search(r"\b(day|morning|نهار|صباح)\b", text, re.I):
            day_night = "day"
    return SettingNode(indoor_outdoor=indoor, day_night=day_night)


def _extract_dialogue(text: str) -> list[str]:
    quotes = re.findall(r"[\"«](.+?)[\"»]", text)
    return [q.strip() for q in quotes if q.strip()]


def _detect_missing_slots(
    people: list[PersonNode],
    setting: SettingNode,
    follow_answers: dict[str, str],
    symbols: list[str],
) -> list[str]:
    missing: list[str] = []
    if people and all(p.known is None for p in people) and "people_identity" not in follow_answers:
        missing.append("people_identity")
    if setting.indoor_outdoor is None and "setting_indoor_outdoor" not in follow_answers:
        missing.append("setting_indoor_outdoor")
    if setting.day_night is None and "setting_day_night" not in follow_answers:
        missing.append("setting_day_night")
    if "observer_or_actor" not in follow_answers:
        missing.append("observer_or_actor")
    if symbols and "symbol_detail" not in follow_answers:
        # Only ask symbol detail if we have a symbol but no detail yet — keep optional unless critical
        pass
    # Preserve critical order
    ordered = [s for s in CRITICAL_SLOTS if s in missing]
    for s in missing:
        if s not in ordered:
            ordered.append(s)
    return ordered
