import pytest

from cidar_robust_fusion import robust_fuse_ranges


def test_robust_fusion_removes_outlier():
    measurements = [
        {"range": 100.0, "confidence": 0.9},
        {"range": 101.0, "confidence": 0.8},
        {"range": 102.0, "confidence": 0.9},
        {"range": 450.0, "confidence": 0.9},
    ]

    result = robust_fuse_ranges(measurements)

    assert result["sensor_count"] == 3
    assert result["fused_range"] < 110.0


def test_robust_fusion_uses_confidence():
    measurements = [
        {"range": 100.0, "confidence": 0.9},
        {"range": 110.0, "confidence": 0.1},
    ]

    result = robust_fuse_ranges(measurements)

    expected = (100.0 * 0.9 + 110.0 * 0.1) / 1.0

    assert result["fused_range"] == pytest.approx(expected)


def test_robust_fusion_returns_uncertainty():
    measurements = [
        {"range": 100.0, "confidence": 0.9},
        {"range": 101.0, "confidence": 0.8},
        {"range": 102.0, "confidence": 0.9},
    ]

    result = robust_fuse_ranges(measurements)

    assert result["uncertainty"] > 0


def test_empty_measurements_fail():
    with pytest.raises(ValueError):
        robust_fuse_ranges([])


def test_invalid_confidence_fails():
    measurements = [
        {"range": 100.0, "confidence": 1.5},
        {"range": 101.0, "confidence": 0.8},
        {"range": 102.0, "confidence": 0.9},
    ]

    with pytest.raises(ValueError):
        robust_fuse_ranges(measurements)