from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PageIndexNode:
    node_id: str
    title: str
    summary: str = ""
    start_page: int | None = None
    end_page: int | None = None
    path: str = ""
    children: list[PageIndexNode] = field(default_factory=list)
    text: str | None = None


@dataclass
class PageIndexTree:
    doc_name: str
    description: str = ""
    roots: list[PageIndexNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        def node_dict(n: PageIndexNode) -> dict[str, Any]:
            return {
                "node_id": n.node_id,
                "title": n.title,
                "summary": n.summary,
                "start_page": n.start_page,
                "end_page": n.end_page,
                "path": n.path,
                "text": n.text,
                "children": [node_dict(c) for c in n.children],
            }

        return {
            "doc_name": self.doc_name,
            "description": self.description,
            "structure": [node_dict(r) for r in self.roots],
        }


def build_simple_tree_from_sections(
    doc_name: str,
    sections: list[tuple[str, str]],
    *,
    description: str = "",
) -> PageIndexTree:
    """
    Offline stand-in for PageIndex SDK: one root chapter with section leaves.
    `sections` is a list of (title, text).
    """
    children: list[PageIndexNode] = []
    for i, (title, text) in enumerate(sections, start=1):
        path = f"1.{i}"
        children.append(
            PageIndexNode(
                node_id=f"n-{i}",
                title=title,
                summary=text[:240],
                path=path,
                text=text,
            )
        )
    root = PageIndexNode(
        node_id="n-root",
        title=doc_name,
        summary=description or doc_name,
        path="1",
        children=children,
    )
    return PageIndexTree(doc_name=doc_name, description=description, roots=[root])


def find_nodes_by_keyword(tree: PageIndexTree, query: str) -> list[PageIndexNode]:
    """Naive tree filter used until LLM tree-nav is wired."""
    q = query.lower()
    hits: list[PageIndexNode] = []

    def walk(node: PageIndexNode) -> None:
        blob = f"{node.title} {node.summary} {node.text or ''}".lower()
        if q in blob or any(tok and tok in blob for tok in q.split()):
            hits.append(node)
        for child in node.children:
            walk(child)

    for root in tree.roots:
        walk(root)
    return hits
