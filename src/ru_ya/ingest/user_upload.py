from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ru_ya.ingest.chunk import TextChunk, chunk_by_logical_units
from ru_ya.ingest.embed import EmbeddingClient, HashEmbeddingClient
from ru_ya.ingest.pageindex_build import PageIndexTree, build_simple_tree_from_sections

PAGEINDEX_PAGE_THRESHOLD = 40


class UserDocStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class AuthorityPreference(str, Enum):
    INFORMATIONAL = "informational"
    PREFERRED_OVERLAY = "preferred_overlay"


@dataclass
class UserDocumentDraft:
    owner_user_id: str
    filename: str
    object_key: str
    status: UserDocStatus = UserDocStatus.PROCESSING
    authority_preference: AuthorityPreference = AuthorityPreference.INFORMATIONAL
    page_count: int | None = None
    chunks: list[TextChunk] = field(default_factory=list)
    embeddings: list[list[float]] = field(default_factory=list)
    pageindex_tree: PageIndexTree | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def process_user_text(
    *,
    owner_user_id: str,
    filename: str,
    object_key: str,
    text: str,
    page_count: int | None = None,
    authority_preference: AuthorityPreference = AuthorityPreference.INFORMATIONAL,
    embedder: EmbeddingClient | None = None,
) -> UserDocumentDraft:
    draft = UserDocumentDraft(
        owner_user_id=owner_user_id,
        filename=filename,
        object_key=object_key,
        authority_preference=authority_preference,
        page_count=page_count,
    )
    try:
        chunks = chunk_by_logical_units(
            text, base_metadata={"source_scope": "user", "filename": filename}
        )
        tree = None
        if page_count is not None and page_count >= PAGEINDEX_PAGE_THRESHOLD:
            pairs = [
                (f"Section {i+1}", c.text_original) for i, c in enumerate(chunks[:50])
            ]
            tree = build_simple_tree_from_sections(filename, pairs)
            for chunk, leaf in zip(chunks, tree.roots[0].children):
                chunk.pageindex_path = leaf.path

        client = embedder or HashEmbeddingClient()
        embeddings = client.embed([c.text_normalized for c in chunks])
        draft.chunks = chunks
        draft.embeddings = embeddings
        draft.pageindex_tree = tree
        draft.status = UserDocStatus.READY
    except Exception as exc:  # noqa: BLE001 — surface as failed draft
        draft.status = UserDocStatus.FAILED
        draft.error_message = str(exc)
    return draft
