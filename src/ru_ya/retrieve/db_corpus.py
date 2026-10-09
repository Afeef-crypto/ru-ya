"""Load curated chunks from Postgres into the in-process corpus used by HybridRetriever."""

from __future__ import annotations

from ru_ya.config import get_settings
from ru_ya.ingest.pageindex_build import PageIndexNode, PageIndexTree
from ru_ya.retrieve.hybrid import CorpusChunk, InMemoryCorpus


def load_corpus_from_db() -> InMemoryCorpus | None:
    settings = get_settings()
    if not settings.database_url:
        return None
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        return None

    corpus = InMemoryCorpus()
    try:
        with psycopg.connect(settings.database_url, connect_timeout=15, row_factory=dict_row) as conn:
            rows = conn.execute(
                """
                select
                    c.id::text as chunk_id,
                    c.text_original,
                    c.text_normalized,
                    c.embedding::text as embedding_text,
                    c.metadata,
                    c.pageindex_path,
                    c.topic_tags,
                    d.author,
                    d.reliability_tier,
                    d.pending_scholar_review,
                    d.title as document_title,
                    d.pageindex_tree,
                    cit.id::text as citation_id,
                    cit.cite_key,
                    cit.grade as hadith_grade
                from chunks c
                join documents d on d.id = c.document_id
                left join citations cit on cit.id = c.citation_id
                where c.embedding is not null
                """
            ).fetchall()
            if not rows:
                return None

            for row in rows:
                emb = _parse_vector(row["embedding_text"])
                meta = dict(row["metadata"] or {})
                meta["topic_tags"] = list(row["topic_tags"] or meta.get("topic_tags") or [])
                meta["document_title"] = row["document_title"]
                corpus.chunks.append(
                    CorpusChunk(
                        chunk_id=row["chunk_id"],
                        text_original=row["text_original"],
                        text_normalized=row["text_normalized"],
                        embedding=emb,
                        reliability_tier=row["reliability_tier"],
                        author=row["author"],
                        citation_id=row["citation_id"],
                        cite_key=row["cite_key"],
                        hadith_grade=row["hadith_grade"],
                        pending_scholar_review=bool(row["pending_scholar_review"]),
                        pageindex_path=row["pageindex_path"],
                        metadata=meta,
                    )
                )
                tree_json = row["pageindex_tree"]
                title = row["document_title"]
                if tree_json and title not in corpus.trees:
                    corpus.trees[title] = _tree_from_json(tree_json)
    except Exception:  # noqa: BLE001
        return None
    return corpus if corpus.chunks else None


def _parse_vector(text: str | None) -> list[float]:
    if not text:
        return [0.0] * 1024
    raw = text.strip()
    if raw.startswith("["):
        raw = raw[1:]
    if raw.endswith("]"):
        raw = raw[:-1]
    if not raw:
        return [0.0] * 1024
    return [float(x) for x in raw.split(",")]


def _tree_from_json(data: dict) -> PageIndexTree:
    def node(n: dict) -> PageIndexNode:
        return PageIndexNode(
            node_id=str(n.get("node_id") or ""),
            title=str(n.get("title") or ""),
            summary=str(n.get("summary") or ""),
            start_page=n.get("start_page"),
            end_page=n.get("end_page"),
            path=str(n.get("path") or ""),
            text=n.get("text"),
            children=[node(c) for c in (n.get("children") or [])],
        )

    roots = [node(r) for r in (data.get("structure") or [])]
    return PageIndexTree(
        doc_name=str(data.get("doc_name") or "document"),
        description=str(data.get("description") or ""),
        roots=roots,
    )
