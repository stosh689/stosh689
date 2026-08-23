from cidar_audit import create_audit_record


def test_audit_record_contains_decision_details():
    record = create_audit_record(
        weights=[1, 1],
        criteria=[0.8, 0.8],
    )

    assert record["weights"] == [1, 1]
    assert record["criteria"] == [0.8, 0.8]
    assert record["weighted_score"] == 0.8
    assert record["threshold"] == 0.70
    assert record["decision"] == "Approved"


def test_audit_record_review_decision():
    record = create_audit_record(
        weights=[1, 1],
        criteria=[0.4, 0.4],
    )

    assert record["weighted_score"] == 0.4
    assert record["decision"] == "Review"


def test_audit_record_preserves_custom_threshold():
    record = create_audit_record(
        weights=[1, 1],
        criteria=[0.75, 0.75],
        threshold=0.80,
    )

    assert record["threshold"] == 0.80
    assert record["decision"] == "Review"