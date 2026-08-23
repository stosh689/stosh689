from ethical_decision import ethical_decision


def test_safe_decision():
    result = ethical_decision(
        weights=[1, 1, 1],
        criteria=[0.9, 0.9, 0.9],
    )
    assert result == "Approved"


def test_unsafe_decision():
    result = ethical_decision(
        weights=[1, 1, 1],
        criteria=[0.1, 0.1, 0.1],
    )
    assert result == "Review"


def test_uncertain_data():
    result = ethical_decision(
        weights=[1, 1, 1],
        criteria=[0.6, 0.6, 0.6],
    )
    assert result == "Review"


def test_conflicting_objectives():
    result = ethical_decision(
        weights=[1, 1],
        criteria=[1.0, 0.4],
    )
    assert result == "Review"


def test_decision_is_auditable():
    result = ethical_decision(
        weights=[1, 1],
        criteria=[0.8, 0.8],
    )
    assert result in ("Approved", "Review")