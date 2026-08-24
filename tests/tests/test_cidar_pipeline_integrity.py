from cidar_pipeline import evaluate_cidar_pipeline
from cidar_audit_integrity import verify_audit_record


def test_pipeline_audit_integrity():
    result = evaluate_cidar_pipeline(
        camera_score=0.90,
        lidar_score=0.85,
        radar_score=0.80,
        thermal_score=0.75,
    )

    audit_hash = result["audit_hash"]

    record = {
        key: value
        for key, value in result.items()
        if key != "audit_hash"
    }

    assert verify_audit_record(record, audit_hash)


def test_pipeline_detects_tampering():
    result = evaluate_cidar_pipeline(
        camera_score=0.90,
        lidar_score=0.85,
        radar_score=0.80,
        thermal_score=0.75,
    )

    audit_hash = result["audit_hash"]

    record = {
        key: value
        for key, value in result.items()
        if key != "audit_hash"
    }

    record["decision"] = "Review"

    assert not verify_audit_record(record, audit_hash)