"""One end-to-end fixture dream: night snake dream → retrieve → verify → conclude."""

from __future__ import annotations

from ru_ya.models.dream import Questionnaire
from ru_ya.orchestrator.session import SessionOrchestrator
from ru_ya.models.session import SessionCreate


def run_snake_night_fixture() -> dict:
    orch = SessionOrchestrator()
    snap = orch.create_session(SessionCreate(language="en", retain=False))
    orch.save_questionnaire(
        snap.id,
        Questionnaire(
            dreamer_state="anxiety",
            dream_time="other_night",
            repetition="once",
            waking_emotion="fear",
            locale_context="urban apartment",
            sensitive_flags=["none"],
        ),
    )
    from ru_ya.models.dream import DreamSubmit, FollowUpAnswers

    snap = orch.submit_dream(
        snap.id,
        DreamSubmit(
            narrative=(
                "I saw a snake indoors at night. A man was there. "
                "I only observed and woke afraid."
            )
        ),
    )
    # Answer any follow-ups to reach ready_to_conclude
    while snap.state.value == "awaiting_followups" and snap.pending_follow_ups:
        answers = {}
        for q in snap.pending_follow_ups:
            slot = q["slot"] if isinstance(q, dict) else q.slot
            if slot == "people_identity":
                answers[slot] = "unknown man"
            elif slot == "setting_indoor_outdoor":
                answers[slot] = "indoors"
            elif slot == "setting_day_night":
                answers[slot] = "night"
            elif slot == "observer_or_actor":
                answers[slot] = "only observe"
            else:
                answers[slot] = "unknown"
        snap = orch.answer_follow_ups(snap.id, FollowUpAnswers(answers=answers))

    events = list(orch.conclude(snap.id))
    conclusion = orch.get_conclusion(snap.id)
    return {
        "session": snap.model_dump(mode="json"),
        "events": events,
        "conclusion": conclusion.model_dump(mode="json"),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_snake_night_fixture(), ensure_ascii=False, indent=2))
