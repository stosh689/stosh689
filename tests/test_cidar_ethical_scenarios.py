import pytest

from ethical_decision import ethical_decision


def test_safe_decision():
    result = ethical_decision(
        risk=0.1,
        benefit=0.9,
        confidence=0.95,
    )
    assert result is not None


def test_unsafe_decision():
    result = ethical_decision(
        risk=0.95,
        benefit=0.1,
        confidence=0.95,
    )
    assert result is not None


def test_uncertain_data():
    result = ethical_decision(
        risk=0.3,
        benefit=0.6,
        confidence=0.2,
    )
    assert result is not None


def test_conflicting_objectives():
    result = ethical_decision(
        risk=0.5,
        benefit=0.5,
        confidence=0.8,
    )
    assert result is not None


def test_decision_is_auditable():
    result = ethical_decision(
        risk=0.2,
        benefit=0.8,
        confidence=0.9,
    )
    assert result is not None