from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator
from uuid import UUID, uuid4

from ru_ya.guardrails.policy import evaluate_guardrails
from ru_ya.models.conclusion import ConclusionPayload
from ru_ya.models.dream import (
    DreamGraph,
    DreamSubmit,
    FollowUpAnswers,
    FollowUpQuestion,
    Questionnaire,
)
from ru_ya.models.session import SessionCreate, SessionSnapshot, SessionState
from ru_ya.parser.dream_parser import parse_dream_narrative
from ru_ya.parser.slots import FOLLOWUP_CATALOG
from ru_ya.retrieve.hybrid import HybridRetriever
from ru_ya.synthesize.conclude import synthesize_conclusion
from ru_ya.verify.cross_source import build_evidence_matrix


@dataclass
class SessionRecord:
    id: UUID
    language: str
    retain: bool
    owner_user_id: str | None
    state: SessionState = SessionState.CREATED
    questionnaire: dict[str, Any] = field(default_factory=dict)
    accumulated_facts: dict[str, Any] = field(default_factory=dict)
    follow_up_round: int = 0
    max_follow_up_rounds: int = 3
    pending_follow_ups: list[FollowUpQuestion] = field(default_factory=list)
    narrative: str | None = None
    dream_graph: DreamGraph | None = None
    conclusion: ConclusionPayload | None = None
    guardrail_flags: list[str] = field(default_factory=list)
    turns: list[dict[str, Any]] = field(default_factory=list)
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24)
    )


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionRecord] = {}

    def create(self, body: SessionCreate) -> SessionRecord:
        record = SessionRecord(
            id=uuid4(),
            language=body.language,
            retain=body.retain,
            owner_user_id=body.owner_user_id,
        )
        self._sessions[record.id] = record
        return record

    def get(self, session_id: UUID) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: UUID) -> bool:
        return self._sessions.pop(session_id, None) is not None


class SessionOrchestrator:
    def __init__(
        self,
        store: InMemorySessionStore | None = None,
        retriever: HybridRetriever | None = None,
    ) -> None:
        self.store = store or InMemorySessionStore()
        self.retriever = retriever or HybridRetriever()

    def create_session(self, body: SessionCreate) -> SessionSnapshot:
        record = self.store.create(body)
        self._add_turn(record, "system", "system", {"event": "created"})
        return self._snapshot(record)

    def save_questionnaire(self, session_id: UUID, questionnaire: Questionnaire) -> SessionSnapshot:
        record = self._require(session_id)
        record.questionnaire = questionnaire.model_dump()
        record.accumulated_facts["questionnaire"] = record.questionnaire
        record.accumulated_facts["sensitivity_flags"] = questionnaire.sensitive_flags
        record.state = SessionState.QUESTIONNAIRE_COMPLETE
        self._add_turn(record, "user", "pre_q", record.questionnaire)
        return self._snapshot(record)

    def submit_dream(self, session_id: UUID, body: DreamSubmit) -> SessionSnapshot:
        record = self._require(session_id)
        if record.state not in {
            SessionState.QUESTIONNAIRE_COMPLETE,
            SessionState.AWAITING_FOLLOWUPS,
            SessionState.READY_TO_CONCLUDE,
        }:
            if record.state == SessionState.CREATED:
                raise ValueError("Complete the questionnaire before submitting a dream")

        guard = evaluate_guardrails(
            narrative=body.narrative,
            questionnaire=record.questionnaire,
            accumulated_facts=record.accumulated_facts,
        )
        if not guard.allowed:
            record.state = SessionState.REFUSED
            record.guardrail_flags = guard.refuse_codes
            record.conclusion = ConclusionPayload(
                conclusion_md=guard.message_en or "",
                abstained=True,
                guardrail_flags=guard.refuse_codes,
            )
            self._add_turn(
                record,
                "assistant",
                "system",
                {"refused": True, "codes": guard.refuse_codes, "message": guard.message_en},
            )
            return self._snapshot(record)

        record.narrative = body.narrative
        record.state = SessionState.DREAM_SUBMITTED
        self._add_turn(record, "user", "dream", {"narrative": body.narrative})
        graph = parse_dream_narrative(
            body.narrative,
            questionnaire=record.questionnaire,
            prior_facts=record.accumulated_facts,
            language=record.language,
        )
        return self._after_parse(record, graph, guard.confidence_ceiling)

    def answer_follow_ups(self, session_id: UUID, body: FollowUpAnswers) -> SessionSnapshot:
        record = self._require(session_id)
        if record.state != SessionState.AWAITING_FOLLOWUPS:
            raise ValueError("Session is not awaiting follow-ups")

        answers = dict(record.accumulated_facts.get("follow_up_answers") or {})
        answers.update({k: v for k, v in body.answers.items() if v is not None})
        record.accumulated_facts["follow_up_answers"] = answers
        record.follow_up_round += 1
        self._add_turn(record, "user", "follow_up", {"answers": body.answers})

        assert record.narrative is not None
        graph = parse_dream_narrative(
            record.narrative,
            questionnaire=record.questionnaire,
            prior_facts=record.accumulated_facts,
            language=record.language,
        )
        # Drop slots just answered
        graph.missing_slots = [s for s in graph.missing_slots if s not in answers]
        return self._after_parse(record, graph, confidence_ceiling=100)

    def conclude(self, session_id: UUID) -> Iterator[dict[str, Any]]:
        record = self._require(session_id)
        if record.state == SessionState.REFUSED:
            yield {"event": "refused", "data": record.conclusion.model_dump() if record.conclusion else {}}
            return
        if record.state not in {
            SessionState.READY_TO_CONCLUDE,
            SessionState.AWAITING_FOLLOWUPS,
            SessionState.DREAM_SUBMITTED,
            SessionState.CONCLUDED,
        }:
            raise ValueError(f"Cannot conclude from state {record.state}")

        # If still awaiting but user forces conclude, mark unknowns
        if record.dream_graph and record.dream_graph.missing_slots:
            record.accumulated_facts["unknown_slots"] = list(record.dream_graph.missing_slots)

        yield {"event": "parsing", "data": {"ok": True}}
        graph = record.dream_graph or DreamGraph()
        record.accumulated_facts["dream_graph"] = graph.model_dump()

        guard = evaluate_guardrails(
            narrative=record.narrative,
            questionnaire=record.questionnaire,
            accumulated_facts=record.accumulated_facts,
        )
        if not guard.allowed:
            record.state = SessionState.REFUSED
            yield {"event": "refused", "data": {"codes": guard.refuse_codes}}
            return

        record.state = SessionState.RETRIEVING
        yield {"event": "retrieving", "data": {}}
        retrieval = self.retriever.retrieve(
            graph, owner_user_id=record.owner_user_id
        )

        record.state = SessionState.VERIFYING
        yield {"event": "verifying", "data": {"hit_count": len(retrieval.hits)}}
        matrix = build_evidence_matrix(retrieval, graph, record.accumulated_facts)

        record.state = SessionState.DRAFTING
        yield {"event": "drafting", "data": {}}
        conclusion = synthesize_conclusion(
            graph=graph,
            retrieval=retrieval,
            matrix=matrix,
            accumulated_facts=record.accumulated_facts,
            confidence_ceiling=guard.confidence_ceiling,
            language=record.language,
        )
        conclusion.guardrail_flags = list(
            dict.fromkeys([*conclusion.guardrail_flags, *guard.sensitive_flags])
        )
        record.conclusion = conclusion
        record.state = SessionState.CONCLUDED
        self._add_turn(record, "assistant", "conclusion", conclusion.model_dump())
        yield {"event": "done", "data": conclusion.model_dump()}

    def get(self, session_id: UUID) -> SessionSnapshot:
        return self._snapshot(self._require(session_id))

    def get_conclusion(self, session_id: UUID) -> ConclusionPayload:
        record = self._require(session_id)
        if record.conclusion is None:
            raise ValueError("No conclusion yet")
        return record.conclusion

    def delete(self, session_id: UUID) -> None:
        if not self.store.delete(session_id):
            raise KeyError("Session not found")

    def _after_parse(
        self,
        record: SessionRecord,
        graph: DreamGraph,
        confidence_ceiling: int,
    ) -> SessionSnapshot:
        _ = confidence_ceiling  # applied at conclude time
        record.dream_graph = graph
        record.accumulated_facts["dream_graph"] = graph.model_dump()
        record.accumulated_facts["sensitivity_flags"] = graph.sensitivity_flags

        if (
            graph.missing_slots
            and record.follow_up_round < record.max_follow_up_rounds
        ):
            pending = [
                FOLLOWUP_CATALOG[s]
                for s in graph.missing_slots
                if s in FOLLOWUP_CATALOG
            ][:3]
            record.pending_follow_ups = pending
            record.state = SessionState.AWAITING_FOLLOWUPS
            self._add_turn(
                record,
                "assistant",
                "follow_up",
                {"questions": [q.model_dump() for q in pending]},
            )
        else:
            if graph.missing_slots:
                record.accumulated_facts["unknown_slots"] = list(graph.missing_slots)
            record.pending_follow_ups = []
            record.state = SessionState.READY_TO_CONCLUDE
        return self._snapshot(record)

    def _require(self, session_id: UUID) -> SessionRecord:
        record = self.store.get(session_id)
        if record is None:
            raise KeyError("Session not found")
        return record

    def _add_turn(
        self,
        record: SessionRecord,
        role: str,
        turn_type: str,
        payload: dict[str, Any],
    ) -> None:
        record.turns.append(
            {
                "role": role,
                "turn_type": turn_type,
                "payload": payload,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _snapshot(self, record: SessionRecord) -> SessionSnapshot:
        return SessionSnapshot(
            id=record.id,
            state=record.state,
            language=record.language,
            questionnaire=record.questionnaire,
            accumulated_facts=record.accumulated_facts,
            follow_up_round=record.follow_up_round,
            max_follow_up_rounds=record.max_follow_up_rounds,
            retain=record.retain,
            expires_at=record.expires_at,
            guardrail_flags=record.guardrail_flags,
            pending_follow_ups=[q.model_dump() for q in record.pending_follow_ups],
        )
