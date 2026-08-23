import hashlib
import json


def generate_audit_hash(record):
    """Generate a deterministic SHA-256 hash for an audit record."""
    canonical = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_audit_record(record, expected_hash):
    """Verify that an audit record has not changed."""
    return generate_audit_hash(record) == expected_hash