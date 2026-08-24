from cidar_audit import create_audit_record
from cidar_audit_integrity import (
    generate_audit_hash,
    verify_audit_record,
)


def test_complete_cidar_decision_pipeline():
    record = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
        threshold=0.70,
    )

    audit_hash = generate_audit_hash(record)

    assert record["decision"] == "Approved"
    assert record["weighted_score"] == 0.83
    assert record["threshold"] == 0.70
    assert verify_audit_record(record, audit_hash)


def test_complete_pipeline_detects_tampering():
    record = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
    )

    audit_hash = generate_audit_hash(record)

    record["decision"] = "Review"

    assert not verify_audit_record(record, audit_hash)