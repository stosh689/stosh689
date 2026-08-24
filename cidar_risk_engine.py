from cidar_audit import create_audit_record
from cidar_audit_integrity import generate_audit_hash


def evaluate_cidar_event(sensor_data):
    """
    Evaluate a CIDAR event from multiple evidence sources.
    """

    weights = [
        sensor_data["camera_weight"],
        sensor_data["lidar_weight"],
        sensor_data["radar_weight"],
        sensor_data["thermal_weight"],
    ]

    criteria = [
        sensor_data["camera_score"],
        sensor_data["lidar_score"],
        sensor_data["radar_score"],
        sensor_data["thermal_score"],
    ]

    audit = create_audit_record(weights, criteria)

    audit["event_type"] = sensor_data["event_type"]
    audit["confidence"] = sensor_data["confidence"]

    audit["audit_hash"] = generate_audit_hash(audit)

    return audit