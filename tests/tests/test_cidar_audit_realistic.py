from cidar_audit import create_audit_record
from cidar_audit_integrity import (
    generate_audit_hash,
    verify_audit_record,
)


def test_approved_decision_has_valid_audit_trail():
    record = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
    )

    audit_hash = generate_audit_hash(record)

    assert record["decision"] == "Approved"
    assert record["weighted_score"] >= record["threshold"]
    assert verify_audit_record(record, audit_hash)


def test_review_decision_has_valid_audit_trail():
    record = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.5, 0.6, 0.7],
    )

    audit_hash = generate_audit_hash(record)

    assert record["decision"] == "Review"
    assert record["weighted_score"] < record["threshold"]
    assert verify_audit_record(record, audit_hash)


def test_audit_detects_decision_record_change():
    record = create_audit_record(
        weights=[4, 3, 2, 1],
        criteria=[0.9, 0.8, 0.7, 0.6],
    )

    audit_hash = generate_audit_hash(record)

    record["criteria"][0] = 0.1

    assert not verify_audit_record(record, audit_hash)