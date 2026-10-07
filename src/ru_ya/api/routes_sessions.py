from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from ru_ya.api.deps import get_orchestrator
from ru_ya.models.dream import DreamSubmit, FollowUpAnswers, Questionnaire
from ru_ya.models.session import SessionCreate, SessionSnapshot
from ru_ya.orchestrator.session import SessionOrchestrator

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionSnapshot)
def create_session(
    body: SessionCreate,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> SessionSnapshot:
    return orch.create_session(body)


@router.get("/{session_id}", response_model=SessionSnapshot)
def get_session(
    session_id: UUID,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> SessionSnapshot:
    try:
        return orch.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{session_id}/questionnaire", response_model=SessionSnapshot)
def put_questionnaire(
    session_id: UUID,
    body: Questionnaire,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> SessionSnapshot:
    try:
        return orch.save_questionnaire(session_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/dream", response_model=SessionSnapshot)
def post_dream(
    session_id: UUID,
    body: DreamSubmit,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> SessionSnapshot:
    try:
        return orch.submit_dream(session_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/follow-ups", response_model=SessionSnapshot)
def post_follow_ups(
    session_id: UUID,
    body: FollowUpAnswers,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> SessionSnapshot:
    try:
        return orch.answer_follow_ups(session_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/conclude")
async def conclude_session(
    session_id: UUID,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> EventSourceResponse:
    def event_generator():
        try:
            for item in orch.conclude(session_id):
                yield {
                    "event": item["event"],
                    "data": json.dumps(item.get("data", {}), ensure_ascii=False),
                }
        except KeyError as exc:
            yield {"event": "error", "data": json.dumps({"detail": str(exc)})}
        except ValueError as exc:
            yield {"event": "error", "data": json.dumps({"detail": str(exc)})}

    return EventSourceResponse(event_generator())


@router.get("/{session_id}/conclusion")
def get_conclusion(
    session_id: UUID,
    orch: SessionOrchestrator = Depends(get_orchestrator),
):
    try:
        return orch.get_conclusion(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: UUID,
    orch: SessionOrchestrator = Depends(get_orchestrator),
) -> None:
    try:
        orch.delete(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
