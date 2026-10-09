"""Ingest seed curated corpus into Postgres."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ru_ya.config import get_settings  # noqa: E402
from ru_ya.ingest.seed_fixture import build_seed_corpus  # noqa: E402


def main() -> int:
    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]", "-q"])
        import psycopg
        from psycopg.types.json import Jsonb

    url = get_settings().database_url
    if not url:
        print("STATUS=missing_database_url")
        return 2

    corpus = build_seed_corpus()
    inserted_docs = 0
    inserted_chunks = 0

    with psycopg.connect(url, connect_timeout=20) as conn:
        for draft in corpus:
            # Upsert-ish: delete prior seed docs with same title
            conn.execute("delete from documents where title = %s", (draft.title,))
            tree = draft.pageindex_tree.to_dict() if draft.pageindex_tree else None
            doc_id = conn.execute(
                """
                insert into documents (
                    title, author, death_year, manhaj_tag, reliability_tier,
                    collection, lang, pending_scholar_review, pageindex_tree, metadata
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                returning id
                """,
                (
                    draft.title,
                    draft.author,
                    draft.death_year,
                    draft.manhaj_tag,
                    draft.reliability_tier,
                    draft.collection,
                    draft.lang,
                    draft.pending_scholar_review,
                    Jsonb(tree) if tree else None,
                    Jsonb(draft.metadata),
                ),
            ).fetchone()[0]
            inserted_docs += 1

            for chunk, emb in zip(draft.chunks, draft.embeddings):
                tags = chunk.metadata.get("topic_tags") or draft.metadata.get("topic_tags") or []
                cite_key = f"{draft.collection or 'seed'}:{chunk.metadata.get('unit_index', 0)}"
                citation_id = conn.execute(
                    """
                    insert into citations (document_id, collection, grade, cite_key, metadata)
                    values (%s,%s,%s,%s,%s)
                    on conflict (cite_key) do update set document_id = excluded.document_id
                    returning id
                    """,
                    (
                        doc_id,
                        draft.collection or "seed",
                        "sahih" if draft.reliability_tier == 1 else None,
                        cite_key,
                        Jsonb({"title": draft.title}),
                    ),
                ).fetchone()[0]

                # pgvector accepts string literal '[1,2,...]'
                emb_lit = "[" + ",".join(f"{x:.8f}" for x in emb) + "]"
                conn.execute(
                    """
                    insert into chunks (
                        document_id, citation_id, text_original, text_normalized,
                        embedding, metadata, pageindex_path, topic_tags
                    ) values (%s,%s,%s,%s,%s::vector,%s,%s,%s)
                    """,
                    (
                        doc_id,
                        citation_id,
                        chunk.text_original,
                        chunk.text_normalized,
                        emb_lit,
                        Jsonb(chunk.metadata),
                        chunk.pageindex_path,
                        tags,
                    ),
                )
                inserted_chunks += 1
        conn.commit()

    print(
        json.dumps(
            {
                "STATUS": "ok",
                "documents": inserted_docs,
                "chunks": inserted_chunks,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
