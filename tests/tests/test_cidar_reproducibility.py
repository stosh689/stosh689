from cidar_audit import create_audit_record
from cidar_audit_integrity import generate_audit_hash


def test_same_inputs_produce_same_audit_record():
    first = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
    )

    second = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
    )

    assert first == second


def test_same_record_produces_same_integrity_hash():
    record = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
    )

    first_hash = generate_audit_hash(record)
    second_hash = generate_audit_hash(record)

    assert first_hash == second_hash


def test_different_inputs_produce_different_hashes():
    first = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
    )

    second = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.8, 0.8, 0.7],
    )

    assert generate_audit_hash(first) != generate_audit_hash(second)