from __future__ import annotations

from functools import lru_cache

from ru_ya.orchestrator.session import SessionOrchestrator
from ru_ya.retrieve.db_corpus import load_corpus_from_db
from ru_ya.retrieve.hybrid import HybridRetriever, InMemoryCorpus


@lru_cache
def get_orchestrator() -> SessionOrchestrator:
    corpus = load_corpus_from_db() or InMemoryCorpus.from_seed()
    retriever = HybridRetriever(corpus=corpus)
    return SessionOrchestrator(retriever=retriever)
