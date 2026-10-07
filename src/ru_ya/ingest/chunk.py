from __future__ import annotations

from dataclasses import dataclass, field

from ru_ya.ingest.normalize import normalize_arabic


@dataclass
class TextChunk:
    text_original: str
    text_normalized: str
    metadata: dict = field(default_factory=dict)
    pageindex_path: str | None = None


def chunk_by_logical_units(
    text: str,
    *,
    separator: str = "\n\n",
    max_chars: int = 1800,
    base_metadata: dict | None = None,
) -> list[TextChunk]:
    """Split on blank lines (or custom separator), then hard-cap long units."""
    base = dict(base_metadata or {})
    raw_parts = [p.strip() for p in text.split(separator) if p.strip()]
    if not raw_parts:
        raw_parts = [text.strip()] if text.strip() else []

    chunks: list[TextChunk] = []
    for i, part in enumerate(raw_parts):
        pieces = _hard_split(part, max_chars)
        for j, piece in enumerate(pieces):
            meta = {**base, "unit_index": i, "part_index": j}
            chunks.append(
                TextChunk(
                    text_original=piece,
                    text_normalized=normalize_arabic(piece),
                    metadata=meta,
                )
            )
    return chunks


def _hard_split(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # Prefer breaking on whitespace
            space = text.rfind(" ", start, end)
            if space > start + max_chars // 2:
                end = space
        out.append(text[start:end].strip())
        start = end
    return [p for p in out if p]
