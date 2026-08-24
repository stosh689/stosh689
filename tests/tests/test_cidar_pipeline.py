from cidar_pipeline import evaluate_cidar_pipeline


def test_complete_cidar_pipeline():
    result = evaluate_cidar_pipeline(
        camera_score=0.90,
        lidar_score=0.85,
        radar_score=0.80,
        thermal_score=0.75,
    )

    assert result["fused_score"] == 0.825
    assert result["decision"] == "Approved"
    assert result["threshold"] == 0.70
    assert "audit_hash" in result
    assert len(result["audit_hash"]) == 64