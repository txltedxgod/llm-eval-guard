import pytest

from eval_guard.hallucination import HallucinationDetector, evaluate_groundedness


def test_grounded_paraphrase_passes():
    context = [
        "FastAPI processes incoming HTTP traffic asynchronously over ASGI using Pydantic v2 schemas."
    ]
    response = "FastAPI handles HTTP traffic asynchronously via ASGI with Pydantic v2 validation."
    report = evaluate_groundedness(context, response)
    assert report.is_grounded is True
    assert report.groundedness_score >= 0.6
    assert report.hallucination_risk <= 0.4
    assert report.total_claims == 1
    assert report.grounded_claims == 1
    assert report.ungrounded_claims == []


def test_numeric_hallucination_flagged_with_missing_anchors():
    context = "In Q3 2025, quarterly revenue rose 12% to $4.2 million."
    response = "In Q3 2025, quarterly revenue jumped 87% to $9.8 million."
    report = evaluate_groundedness(context, response)
    assert report.is_grounded is False
    assert len(report.ungrounded_claims) == 1
    verdict = report.ungrounded_claims[0]
    assert "87%" in verdict.missing_anchors
    assert "9.8" in verdict.missing_anchors
    assert "Unsupported factual anchors" in verdict.reason


def test_negation_polarity_contradiction_detected():
    context = "The guardrail gateway does not persist plaintext user passwords in logs."
    response = "The guardrail gateway stores plaintext user passwords directly in logs."
    report = evaluate_groundedness(context, response)
    assert report.is_grounded is False
    assert report.ungrounded_claims[0].reason == "Polarity contradiction against source context"
    assert report.ungrounded_claims[0].support_score <= 0.2


def test_partial_hallucination_in_multi_claim_response():
    context = ["Python 3.11 introduced Faster CPython optimizations across standard operations."]
    response = (
        "Python 3.11 introduced Faster CPython optimizations. "
        "It was exclusively developed by NASA in 1998 for telemetry."
    )
    report = evaluate_groundedness(context, response)
    assert report.is_grounded is False
    assert report.total_claims == 2
    assert report.grounded_claims == 1
    assert len(report.ungrounded_claims) == 1
    assert "1998" in report.ungrounded_claims[0].missing_anchors
    assert "NASA" in report.ungrounded_claims[0].missing_anchors


def test_empty_context_returns_zero_groundedness():
    report = evaluate_groundedness([], "The service supports 100k concurrent WebSocket sessions.")
    assert report.is_grounded is False
    assert report.groundedness_score == 0.0
    assert report.hallucination_risk == 1.0
    assert report.grounded_claims == 0


def test_comma_formatted_numbers_match_unformatted():
    context = "The dataset holds 1,250,000 verified telemetry samples."
    response = "The dataset holds 1250000 verified telemetry samples."
    report = evaluate_groundedness(context, response)
    assert report.is_grounded is True
    assert report.ungrounded_claims == []


def test_invalid_inputs_raise_value_error():
    detector = HallucinationDetector()
    with pytest.raises(ValueError, match="non-empty"):
        detector.evaluate("valid context", "   ")
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        HallucinationDetector(min_groundedness=1.5)
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        detector.evaluate("ctx", "Some grounded claim here.", min_groundedness=-0.1)
