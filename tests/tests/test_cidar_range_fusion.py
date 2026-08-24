import pytest

from cidar_range_fusion import fuse_ranges


def test_fuse_ranges_with_equal_confidence():
    measurements = [
        {"range": 100.0, "confidence": 1.0},
        {"range": 102.0, "confidence": 1.0},
    ]

    result = fuse_ranges(measurements)

    assert result["fused_range"] == pytest.approx(101.0)
    assert result["sensor_count"] == 2
    assert result["uncertainty"] > 0


def test_fuse_ranges_uses_confidence_weighting():
    measurements = [
        {"range": 100.0, "confidence": 0.9},
        {"range": 120.0, "confidence": 0.1},
    ]

    result = fuse_ranges(measurements)

    expected = (100.0 * 0.9 + 120.0 * 0.1) / 1.0

    assert result["fused_range"] == pytest.approx(expected)


def test_fuse_ranges_rejects_empty_input():
    with pytest.raises(ValueError):
        fuse_ranges([])


def test_fuse_ranges_rejects_negative_range():
    measurements = [
        {"range": -10.0, "confidence": 1.0},
    ]

    with pytest.raises(ValueError):
        fuse_ranges(measurements)


def test_fuse_ranges_rejects_invalid_confidence():
    measurements = [
        {"range": 100.0, "confidence": 1.5},
    ]

    with pytest.raises(ValueError):
        fuse_ranges(measurements)


def test_fuse_ranges_rejects_zero_total_confidence():
    measurements = [
        {"range": 100.0, "confidence": 0.0},
        {"range": 200.0, "confidence": 0.0},
    ]

    with pytest.raises(ValueError):
        fuse_ranges(measurements)


def test_fuse_ranges_reports_sensor_count():
    measurements = [
        {"range": 100.0, "confidence": 0.8},
        {"range": 105.0, "confidence": 0.9},
        {"range": 98.0, "confidence": 0.7},
    ]

    result = fuse_ranges(measurements)

    assert result["sensor_count"] == 3