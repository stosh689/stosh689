from cidar_uncertainty import confidence_adjusted_score


def fuse_confidence_adjusted_evidence(
    camera_score,
    camera_confidence,
    lidar_score,
    lidar_confidence,
    radar_score,
    radar_confidence,
    thermal_score,
    thermal_confidence,
):
    """Fuse sensor evidence after adjusting each measurement by confidence."""

    adjusted_scores = [
        confidence_adjusted_score(camera_score, camera_confidence),
        confidence_adjusted_score(lidar_score, lidar_confidence),
        confidence_adjusted_score(radar_score, radar_confidence),
        confidence_adjusted_score(thermal_score, thermal_confidence),
    ]

    return round(sum(adjusted_scores) / len(adjusted_scores), 10)