from ru_ya.models.dream import DreamGraph, SettingNode
from ru_ya.retrieve.hybrid import HybridRetriever
from ru_ya.verify.confidence import score_confidence
from ru_ya.verify.cross_source import build_evidence_matrix


def test_hybrid_retrieve_seed_and_confidence():
    retriever = HybridRetriever()
    graph = DreamGraph(
        symbols=["snake"],
        actions=["seeing"],
        setting=SettingNode(indoor_outdoor="indoors", day_night="night"),
        missing_slots=[],
    )
    result = retriever.retrieve(graph)
    assert result.queries
    assert result.hits, "seed corpus should return hits"
    matrix = build_evidence_matrix(result, graph, {"unknown_slots": []})
    conf = score_confidence(
        graph=graph,
        retrieval=result,
        matrix=matrix,
        accumulated_facts={"unknown_slots": []},
    )
    assert 0 <= conf.score <= 100
