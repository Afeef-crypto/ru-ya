from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ru_ya.ingest.chunk import TextChunk, chunk_by_logical_units
from ru_ya.ingest.embed import EmbeddingClient, HashEmbeddingClient
from ru_ya.ingest.pageindex_build import PageIndexTree, build_simple_tree_from_sections


@dataclass
class CuratedDocumentDraft:
    title: str
    author: str | None
    reliability_tier: int
    collection: str | None = None
    lang: str = "ar"
    death_year: int | None = None
    manhaj_tag: str | None = None
    pending_scholar_review: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[TextChunk] = field(default_factory=list)
    pageindex_tree: PageIndexTree | None = None
    embeddings: list[list[float]] = field(default_factory=list)


def prepare_curated_document(
    *,
    title: str,
    author: str | None,
    reliability_tier: int,
    text: str,
    collection: str | None = None,
    topic_tags: list[str] | None = None,
    build_pageindex: bool = False,
    section_pairs: list[tuple[str, str]] | None = None,
    embedder: EmbeddingClient | None = None,
) -> CuratedDocumentDraft:
    if reliability_tier not in (1, 2, 3):
        raise ValueError("reliability_tier must be 1, 2, or 3")

    base_meta = {"topic_tags": topic_tags or []}
    chunks = chunk_by_logical_units(text, base_metadata=base_meta)
    tree = None
    if build_pageindex and section_pairs:
        tree = build_simple_tree_from_sections(title, section_pairs)
        # Attach paths to chunks by order when counts match loosely
        leaves = []
        for root in tree.roots:
            leaves.extend(root.children)
        for chunk, leaf in zip(chunks, leaves):
            chunk.pageindex_path = leaf.path
            chunk.metadata["pageindex_node_id"] = leaf.node_id

    client = embedder or HashEmbeddingClient()
    embeddings = client.embed([c.text_normalized for c in chunks])

    return CuratedDocumentDraft(
        title=title,
        author=author,
        reliability_tier=reliability_tier,
        collection=collection,
        metadata=base_meta,
        chunks=chunks,
        pageindex_tree=tree,
        embeddings=embeddings,
    )
