import pytest

from ethical_decision import ethical_decision


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        ethical_decision(
            weights=[1, 1],
            criteria=[0.8],
        )


def test_rejects_empty_inputs():
    with pytest.raises(ValueError):
        ethical_decision(
            weights=[],
            criteria=[],
        )


def test_rejects_zero_total_weight():
    with pytest.raises(ValueError):
        ethical_decision(
            weights=[0, 0],
            criteria=[0.8, 0.9],
        )