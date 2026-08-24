from cidar_sensor_fusion import fuse_sensor_evidence
from cidar_audit import create_audit_record
from cidar_audit_integrity import generate_audit_hash


def evaluate_cidar_pipeline(
    camera_score,
    lidar_score,
    radar_score,
    thermal_score,
):
    """Run sensor fusion, ethical decision, and audit integrity."""

    fused_score = fuse_sensor_evidence(
        camera_score,
        lidar_score,
        radar_score,
        thermal_score,
    )

    record = create_audit_record(
        weights=[1, 1, 1, 1],
        criteria=[
            camera_score,
            lidar_score,
            radar_score,
            thermal_score,
        ],
    )

    record["fused_score"] = fused_score
    record["audit_hash"] = generate_audit_hash(record)

    return record