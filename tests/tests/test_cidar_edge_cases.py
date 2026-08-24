from cidar_audit import create_audit_record
from cidar_audit_integrity import (
    generate_audit_hash,
    verify_audit_record,
)


def test_all_criteria_at_zero():
    record = create_audit_record(
        weights=[1, 1, 1],
        criteria=[0.0, 0.0, 0.0],
    )

    assert record["weighted_score"] == 0.0
    assert record["decision"] == "Review"


def test_all_criteria_at_one():
    record = create_audit_record(
        weights=[1, 1, 1],
        criteria=[1.0, 1.0, 1.0],
    )

    assert record["weighted_score"] == 1.0
    assert record["decision"] == "Approved"


def test_edge_case_audit_remains_verifiable():
    record = create_audit_record(
        weights=[1, 1],
        criteria=[0.0, 1.0],
    )

    audit_hash = generate_audit_hash(record)

    assert verify_audit_record(record, audit_hash)