"""CIDAR sensor evidence fusion.
Combines normalized evidence scores from camera, LiDAR, radar,
and thermal sensors into one deterministic confidence score.
"""
from __future__ import annotations
def fuse_sensor_evidence(
    camera_score: float,
    lidar_score: float,
    radar_score: float,
    thermal_score: float,
) -> float:
    """Return the arithmetic mean of four sensor evidence scores.
    Scores must be finite numeric values in the inclusive range [0, 1].
    """
    scores = [
        float(camera_score),
        float(lidar_score),
        float(radar_score),
        float(thermal_score),
    ]
    for score in scores:
        if not 0.0 <= score <= 1.0:
            raise ValueError("sensor scores must be between 0 and 1")
    return sum(scores) / len(scores)