import pytest

from cidar_uncertainty import confidence_adjusted_score


def test_high_confidence_preserves_score():
    assert confidence_adjusted_score(0.90, 1.0) == 0.90


def test_lower_confidence_reduces_score():
    assert confidence_adjusted_score(0.90, 0.80) == 0.72


def test_zero_confidence_produces_zero():
    assert confidence_adjusted_score(0.90, 0.0) == 0.0


def test_rejects_invalid_score():
    with pytest.raises(ValueError):
        confidence_adjusted_score(1.1, 0.9)


def test_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        confidence_adjusted_score(0.9, 1.1)