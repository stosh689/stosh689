def fuse_ranges(measurements):
    """
    Fuse range measurements using confidence weighting.

    measurements:
        [
            {"range": 100.0, "confidence": 0.9},
            {"range": 102.0, "confidence": 0.8},
        ]
    """

    if not measurements:
        raise ValueError("measurements cannot be empty")

    weighted_sum = 0.0
    confidence_sum = 0.0

    for measurement in measurements:
        if "range" not in measurement or "confidence" not in measurement:
            raise ValueError("each measurement requires range and confidence")

        range_value = float(measurement["range"])
        confidence = float(measurement["confidence"])

        if range_value < 0:
            raise ValueError("range cannot be negative")

        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        weighted_sum += range_value * confidence
        confidence_sum += confidence

    if confidence_sum == 0:
        raise ValueError("total confidence must be greater than zero")

    fused_range = weighted_sum / confidence_sum

    uncertainty = 1.0 / confidence_sum

    return {
        "fused_range": fused_range,
        "uncertainty": uncertainty,
        "sensor_count": len(measurements),
    }


if __name__ == "__main__":
    measurements = [
        {"range": 100.0, "confidence": 0.9},
        {"range": 102.0, "confidence": 0.8},
        {"range": 99.0, "confidence": 0.95},
    ]

    print(fuse_ranges(measurements))