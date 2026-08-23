from ethical_decision import ethical_decision


def test_below_threshold_is_review():
    result = ethical_decision(
        weights=[1],
        criteria=[0.69],
    )
    assert result == "Review"


def test_at_threshold_is_approved():
    result = ethical_decision(
        weights=[1],
        criteria=[0.70],
    )
    assert result == "Approved"


def test_above_threshold_is_approved():
    result = ethical_decision(
        weights=[1],
        criteria=[0.71],
    )
    assert result == "Approved"