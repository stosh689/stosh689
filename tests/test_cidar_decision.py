from ethical_decision import ethical_decision


def test_cidar_approves_strong_case():
    result = ethical_decision(
        weights=[0.4, 0.35, 0.25],
        criteria=[1.0, 0.9, 0.8],
        threshold=0.70,
    )

    assert result == "Approved"


def test_cidar_reviews_weak_case():
    result = ethical_decision(
        weights=[0.4, 0.35, 0.25],
        criteria=[0.2, 0.3, 0.1],
        threshold=0.70,
    )

    assert result == "Review"


def test_cidar_rejects_invalid_inputs():
    try:
        ethical_decision(
            weights=[0.5],
            criteria=[1.0, 0.5],
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError for mismatched inputs"
    )
    
    
    