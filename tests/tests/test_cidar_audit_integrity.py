from cidar_audit_integrity import (
    generate_audit_hash,
    verify_audit_record,
)


def test_audit_hash_is_deterministic():
    record = {
        "decision": "Approved",
        "threshold": 0.70,
        "weighted_score": 0.80,
    }

    first = generate_audit_hash(record)
    second = generate_audit_hash(record)

    assert first == second


def test_unchanged_record_verifies():
    record = {
        "decision": "Approved",
        "threshold": 0.70,
        "weighted_score": 0.80,
    }

    audit_hash = generate_audit_hash(record)

    assert verify_audit_record(record, audit_hash)


def test_modified_record_fails_verification():
    record = {
        "decision": "Approved",
        "threshold": 0.70,
        "weighted_score": 0.80,
    }

    audit_hash = generate_audit_hash(record)

    record["decision"] = "Review"

    assert not verify_audit_record(record, audit_hash)