from ru_ya.guardrails.policy import evaluate_guardrails


def test_refuse_fiqh_request():
    decision = evaluate_guardrails(narrative="Please give me a fatwa: is this haram?")
    assert decision.allowed is False
    assert "refuse_fiqh_ruling" in decision.refuse_codes


def test_sensitive_prophet_ceiling():
    decision = evaluate_guardrails(
        questionnaire={"sensitive_flags": ["prophet"]},
        narrative="I saw something peaceful.",
    )
    assert decision.allowed is True
    assert decision.confidence_ceiling <= 55
