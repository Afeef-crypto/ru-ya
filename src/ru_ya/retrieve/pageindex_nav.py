from __future__ import annotations

from ru_ya.ingest.pageindex_build import PageIndexNode, PageIndexTree, find_nodes_by_keyword


def navigate_tree(tree: PageIndexTree, query: str, *, limit: int = 5) -> list[PageIndexNode]:
    """
    Stub for LLM tree navigation: keyword/path heuristic.
    Production will prompt an LLM with titles/summaries and return node IDs.
    """
    nodes = find_nodes_by_keyword(tree, query)
    return nodes[:limit]
