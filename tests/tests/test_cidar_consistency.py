import pytest

from ethical_decision import ethical_decision


@pytest.mark.parametrize(
    "weights, criteria, expected",
    [
        ([1, 1], [1.0, 1.0], "Approved"),
        ([1, 1], [0.0, 0.0], "Review"),
        ([2, 1], [1.0, 0.0], "Approved"),
        ([1, 2], [0.0, 1.0], "Approved"),
        ([3, 1], [0.6, 0.6], "Review"),
        ([3, 1], [0.8, 0.4], "Approved"),
    ],
)
def test_weighted_decision_consistency(weights, criteria, expected):
    assert ethical_decision(
        weights=weights,
        criteria=criteria,
    ) == expected