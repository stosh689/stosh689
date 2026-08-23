from ethical_decision import ethical_decision


def test_high_weight_criterion_controls_decision():
    result = ethical_decision(
        weights=[9, 1],
        criteria=[0.8, 0.0],
    )
    assert result == "Approved"


def test_low_weight_criterion_does_not_override_high_weight():
    result = ethical_decision(
        weights=[9, 1],
        criteria=[0.8, 0.0],
        threshold=0.70,
    )
    assert result == "Approved"


def test_weighted_score_can_require_review():
    result = ethical_decision(
        weights=[9, 1],
        criteria=[0.6, 0.9],
        threshold=0.70,
    )
    assert result == "Review"