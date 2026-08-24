from cidar_confidence_fusion import fuse_confidence_adjusted_evidence


def test_full_confidence_preserves_sensor_scores():
    result = fuse_confidence_adjusted_evidence(
        0.9, 1.0,
        0.8, 1.0,
        0.7, 1.0,
        0.6, 1.0,
    )

    assert result == 0.75


def test_low_confidence_reduces_fused_evidence():
    result = fuse_confidence_adjusted_evidence(
        0.9, 0.5,
        0.8, 0.5,
        0.7, 0.5,
        0.6, 0.5,
    )

    assert result == 0.375


def test_zero_confidence_produces_zero_evidence():
    result = fuse_confidence_adjusted_evidence(
        0.9, 0.0,
        0.8, 0.0,
        0.7, 0.0,
        0.6, 0.0,
    )

    assert result == 0.0