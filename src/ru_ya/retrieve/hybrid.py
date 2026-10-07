from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from ru_ya.ingest.embed import EmbeddingClient, HashEmbeddingClient
from ru_ya.ingest.normalize import normalize_arabic
from ru_ya.ingest.pageindex_build import PageIndexTree
from ru_ya.ingest.seed_fixture import build_seed_corpus
from ru_ya.models.dream import DreamGraph
from ru_ya.models.retrieval import MergedHit, RetrievalResult
from ru_ya.retrieve.merge import merge_hits, tier_boost
from ru_ya.retrieve.pageindex_nav import navigate_tree


@dataclass
class CorpusChunk:
    chunk_id: str
    text_original: str
    text_normalized: str
    embedding: list[float]
    source_scope: str = "curated"
    reliability_tier: int | None = 1
    author: str | None = None
    citation_id: str | None = None
    cite_key: str | None = None
    hadith_grade: str | None = None
    pending_scholar_review: bool = True
    pageindex_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    owner_user_id: str | None = None


@dataclass
class InMemoryCorpus:
    chunks: list[CorpusChunk] = field(default_factory=list)
    trees: dict[str, PageIndexTree] = field(default_factory=dict)

    @classmethod
    def from_seed(cls, embedder: EmbeddingClient | None = None) -> InMemoryCorpus:
        client = embedder or HashEmbeddingClient()
        corpus = cls()
        for doc in build_seed_corpus():
            doc_key = doc.title
            if doc.pageindex_tree:
                corpus.trees[doc_key] = doc.pageindex_tree
            for chunk, emb in zip(doc.chunks, doc.embeddings):
                cid = str(uuid4())
                cite_key = f"{doc.collection or 'seed'}:{chunk.metadata.get('unit_index', 0)}"
                corpus.chunks.append(
                    CorpusChunk(
                        chunk_id=cid,
                        text_original=chunk.text_original,
                        text_normalized=chunk.text_normalized,
                        embedding=emb,
                        reliability_tier=doc.reliability_tier,
                        author=doc.author,
                        citation_id=cid,
                        cite_key=cite_key,
                        hadith_grade="sahih" if doc.reliability_tier == 1 else None,
                        pending_scholar_review=doc.pending_scholar_review,
                        pageindex_path=chunk.pageindex_path,
                        metadata={**chunk.metadata, "document_title": doc.title},
                    )
                )
        # Warm embedder reference unused beyond seed build
        _ = client
        return corpus


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return max(0.0, min(1.0, (dot / (na * nb) + 1) / 2))  # map roughly to [0,1]


class HybridRetriever:
    def __init__(
        self,
        corpus: InMemoryCorpus | None = None,
        embedder: EmbeddingClient | None = None,
        *,
        alpha: float = 0.45,
        beta: float = 0.30,
        gamma: float = 0.15,
        delta: float = 0.10,
    ) -> None:
        self.embedder = embedder or HashEmbeddingClient()
        self.corpus = corpus or InMemoryCorpus.from_seed(self.embedder)
        self.weights = {"alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta}

    def retrieve(
        self,
        graph: DreamGraph,
        *,
        owner_user_id: str | None = None,
        user_pref_boost: bool = False,
        top_k: int = 12,
    ) -> RetrievalResult:
        queries = self._build_queries(graph)
        raw_hits: list[MergedHit] = []
        for q in queries:
            raw_hits.extend(self._vector_search(q, owner_user_id=owner_user_id, user_pref_boost=user_pref_boost))
            raw_hits.extend(self._pageindex_search(q))

        merged = merge_hits(raw_hits, weights=self.weights, top_k=top_k)
        return RetrievalResult(
            queries=queries,
            hits=merged,
            filters={"owner_user_id": owner_user_id, "weights": self.weights},
        )

    def _build_queries(self, graph: DreamGraph) -> list[str]:
        queries = ["رؤيا حلم حديث النفس أدب الرؤيا", "ru'ya hulm hadith al-nafs dream adab"]
        for symbol in graph.symbols:
            queries.append(symbol)
            queries.append(f"تفسير {symbol}")
        for action in graph.actions:
            queries.append(action)
        if graph.setting.day_night:
            queries.append(graph.setting.day_night)
        if graph.setting.indoor_outdoor:
            queries.append(graph.setting.indoor_outdoor)
        # Dedupe preserve order
        seen: set[str] = set()
        out: list[str] = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                out.append(q)
        return out

    def _vector_search(
        self,
        query: str,
        *,
        owner_user_id: str | None,
        user_pref_boost: bool,
        k: int = 5,
    ) -> list[MergedHit]:
        q_emb = self.embedder.embed([normalize_arabic(query)])[0]
        scored: list[tuple[float, CorpusChunk]] = []
        for chunk in self.corpus.chunks:
            if chunk.source_scope == "user" and chunk.owner_user_id != owner_user_id:
                continue
            sim = _cosine(q_emb, chunk.embedding)
            scored.append((sim, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        hits: list[MergedHit] = []
        for sim, chunk in scored[:k]:
            pref = 0.8 if (chunk.source_scope == "user" and user_pref_boost) else (
                0.3 if chunk.source_scope == "user" else 0.0
            )
            hits.append(
                MergedHit(
                    chunk_id=chunk.chunk_id,
                    source_scope="user" if chunk.source_scope == "user" else "curated",
                    text_original=chunk.text_original,
                    score=0.0,
                    semantic=sim,
                    tier_boost=tier_boost(chunk.reliability_tier),
                    pageindex_confidence=0.0,
                    user_pref=pref,
                    reliability_tier=chunk.reliability_tier,
                    author=chunk.author,
                    citation_id=chunk.citation_id,
                    cite_key=chunk.cite_key,
                    hadith_grade=chunk.hadith_grade,
                    pending_scholar_review=chunk.pending_scholar_review,
                    pageindex_path=chunk.pageindex_path,
                    metadata=chunk.metadata,
                    query=query,
                )
            )
        return hits

    def _pageindex_search(self, query: str) -> list[MergedHit]:
        hits: list[MergedHit] = []
        for doc_name, tree in self.corpus.trees.items():
            nodes = navigate_tree(tree, query, limit=3)
            for node in nodes:
                # Map to chunks with matching path when possible
                matched = [
                    c for c in self.corpus.chunks if c.pageindex_path == node.path
                ]
                if not matched and node.text:
                    # Synthetic hit from node text
                    hits.append(
                        MergedHit(
                            chunk_id=f"pi:{doc_name}:{node.node_id}",
                            source_scope="curated",
                            text_original=node.text,
                            score=0.0,
                            semantic=0.55,
                            tier_boost=1.0,
                            pageindex_confidence=0.85,
                            user_pref=0.0,
                            reliability_tier=1,
                            author="Ibn Hajar",
                            citation_id=None,
                            cite_key=f"pageindex:{node.path}",
                            pending_scholar_review=True,
                            pageindex_path=node.path,
                            metadata={"document_title": doc_name, "node_title": node.title},
                            query=query,
                        )
                    )
                    continue
                for chunk in matched:
                    hits.append(
                        MergedHit(
                            chunk_id=chunk.chunk_id,
                            source_scope="curated",
                            text_original=chunk.text_original,
                            score=0.0,
                            semantic=0.5,
                            tier_boost=tier_boost(chunk.reliability_tier),
                            pageindex_confidence=0.9,
                            user_pref=0.0,
                            reliability_tier=chunk.reliability_tier,
                            author=chunk.author,
                            citation_id=chunk.citation_id,
                            cite_key=chunk.cite_key,
                            hadith_grade=chunk.hadith_grade,
                            pending_scholar_review=chunk.pending_scholar_review,
                            pageindex_path=chunk.pageindex_path,
                            metadata=chunk.metadata,
                            query=query,
                        )
                    )
        return hits
