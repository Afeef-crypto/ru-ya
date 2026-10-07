from ru_ya.retrieve.demo_fixture import run_snake_night_fixture


def test_snake_night_end_to_end():
    result = run_snake_night_fixture()
    assert result["session"]["state"] in {"ready_to_conclude", "awaiting_followups", "concluded"}
    # After conclude in fixture, conclusion must exist
    conclusion = result["conclusion"]
    assert "confidence" in conclusion
    assert 0 <= conclusion["confidence"]["score"] <= 100
    assert any(e["event"] == "done" for e in result["events"])
    # Cite-or-abstain: if claims exist they have citations
    for claim in conclusion.get("claims", []):
        assert claim["citation_ids"], "claims must carry citations"
