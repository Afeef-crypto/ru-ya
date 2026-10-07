from __future__ import annotations

from functools import lru_cache

from ru_ya.orchestrator.session import SessionOrchestrator


@lru_cache
def get_orchestrator() -> SessionOrchestrator:
    return SessionOrchestrator()
