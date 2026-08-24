"""
CIDAR Robust Fusion

Combines robust outlier rejection with confidence-weighted
multi-sensor range fusion.
"""

from cidar_outlier_rejection import reject_outliers


def robust_fuse_ranges(measurements, threshold=3.5):
    """
    Reject range outliers and confidence-weight the remaining sensors.

    measurements:
        [
            {"range": 100.0, "confidence": 0.9},
            {"range": 101.0, "confidence": 0.8},
            {"range": 450.0, "confidence": 0.7},
        ]
    """

    if not measurements:
        raise ValueError("measurements cannot be empty")

    ranges = []

    for measurement in measurements:
        if "range" not in measurement:
            raise ValueError("each measurement requires range")

        if "confidence" not in measurement:
            raise ValueError("each measurement requires confidence")

        ranges.append(float(measurement["range"]))

    filtered_ranges = reject_outliers(
        ranges,
        threshold=threshold,
    )

    filtered_measurements = []

    for measurement in measurements:
        if float(measurement["range"]) in filtered_ranges:
            filtered_measurements.append(measurement)

    if not filtered_measurements:
        raise ValueError("no valid measurements remain")

    weighted_sum = 0.0
    confidence_sum = 0.0

    for measurement in filtered_measurements:
        range_value = float(measurement["range"])
        confidence = float(measurement["confidence"])

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        weighted_sum += range_value * confidence
        confidence_sum += confidence

    if confidence_sum <= 0:
        raise ValueError(
            "total confidence must be greater than zero"
        )

    fused_range = weighted_sum / confidence_sum

    uncertainty = 1.0 / confidence_sum

    return {
        "fused_range": fused_range,
        "uncertainty": uncertainty,
        "sensor_count": len(filtered_measurements),
    }