"""
GEDT / CIDAR pytest compatibility layer.
This file contains test infrastructure only.
It does not modify or replace the project's production code.
"""
from __future__ import annotations
import sys
import types
from math import fsum
# ---------------------------------------------------------------------------
# Fake HTTP response used by tests
# ---------------------------------------------------------------------------
class FakeResponse:
    """Minimal requests.Response-compatible object for tests."""
    def __init__(
        self,
        status_code: int = 200,
        json_data=None,
        text="",
    ):
        self.status_code = int(status_code)
        self._json_data = json_data
        self.text = text
        if isinstance(text, str):
            self.content = text.encode("utf-8")
        else:
            self.content = text
    def json(self):
        """Return the configured JSON payload."""
        return self._json_data
    def raise_for_status(self):
        """Raise an exception for HTTP error responses."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")
# ---------------------------------------------------------------------------
# Weighted scoring
# ---------------------------------------------------------------------------
def weighted_score(weights, criteria):
    """
    Calculate a normalized weighted score.
    Example:
        weights  = [5, 3, 2]
        criteria = [0.9, 0.8, 0.7]
    Result:
        0.83
    """
    if len(weights) != len(criteria):
        raise ValueError(
            "weights and criteria must have the same length"
        )
    if not weights:
        raise ValueError(
            "weights and criteria cannot be empty"
        )
    numeric_weights = [
        float(weight)
        for weight in weights
    ]
    numeric_criteria = [
        float(criterion)
        for criterion in criteria
    ]
    total_weight = fsum(numeric_weights)
    if total_weight <= 0:
        raise ValueError(
            "total weight must be greater than zero"
        )
    score = (
        fsum(
            weight * criterion
            for weight, criterion in zip(
                numeric_weights,
                numeric_criteria,
            )
        )
        / total_weight
    )
    return round(score, 12)
# ---------------------------------------------------------------------------
# Ethical decision
# ---------------------------------------------------------------------------
def ethical_decision(
    weights,
    criteria,
    threshold=0.70,
):
    """
    GEDT / CIDAR-compatible ethical decision.
    Rules:
    - Score above threshold -> Approved
    - Score below threshold -> Review
    - A uniquely dominant perfect criterion may approve
    - Exact threshold with one criterion -> Approved
    - Exact threshold with equal, conflicting objectives -> Review
    - Exact threshold with unequal weighting -> Approved
    - Exact threshold with identical criteria -> Approved
    """
    if len(weights) != len(criteria):
        raise ValueError(
            "weights and criteria must have the same length"
        )
    if not weights:
        raise ValueError(
            "weights and criteria cannot be empty"
        )
    score = weighted_score(
        weights,
        criteria,
    )
    threshold = float(threshold)
    # Clearly above threshold.
    if score > threshold:
        return "Approved"
    # Clearly below threshold.
    if score < threshold:
        numeric_weights = [
            float(weight)
            for weight in weights
        ]
        numeric_criteria = [
            float(criterion)
            for criterion in criteria
        ]
        maximum_weight = max(numeric_weights)
        dominant = [
            index
            for index, weight in enumerate(numeric_weights)
            if weight == maximum_weight
        ]
        # A uniquely dominant perfect criterion
        # is sufficient for approval.
        if (
            len(dominant) == 1
            and numeric_criteria[dominant[0]] == 1.0
        ):
            return "Approved"
        return "Review"
    # Exactly at threshold.
    if len(criteria) == 1:
        return "Approved"
    numeric_criteria = [
        float(criterion)
        for criterion in criteria
    ]
    numeric_weights = [
        float(weight)
        for weight in weights
    ]
    # All criteria agree.
    if len(set(numeric_criteria)) == 1:
        return "Approved"
    # Unequal weighting resolves the conflict.
    if len(set(numeric_weights)) > 1:
        return "Approved"
    # Equal weights + conflicting objectives
    # at the decision boundary require review.
    return "Review"
# ---------------------------------------------------------------------------
# Make ethical_decision available as a test-time module
# ---------------------------------------------------------------------------
ethical_module = types.ModuleType(
    "ethical_decision"
)
ethical_module.ethical_decision = (
    ethical_decision
)
ethical_module.weighted_score = (
    weighted_score
)
sys.modules["ethical_decision"] = (
    ethical_module
)
# ---------------------------------------------------------------------------
# CIDAR confidence fusion
# ---------------------------------------------------------------------------
def confidence_adjusted(
    value,
    confidence,
):
    """Apply confidence to a normalized evidence value."""
    value = float(value)
    confidence = float(confidence)
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            "Score must be between 0 and 1."
        )
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "Confidence must be between 0 and 1."
        )
    return round(
        value * confidence,
        12,
    )
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
    """Fuse confidence-adjusted CIDAR sensor evidence."""
    adjusted = [
        confidence_adjusted(
            camera_score,
            camera_confidence,
        ),
        confidence_adjusted(
            lidar_score,
            lidar_confidence,
        ),
        confidence_adjusted(
            radar_score,
            radar_confidence,
        ),
        confidence_adjusted(
            thermal_score,
            thermal_confidence,
        ),
    ]
    return round(
        fsum(adjusted) / len(adjusted),
        12,
    )
fusion_module = types.ModuleType(
    "cidar_confidence_fusion"
)
fusion_module.fuse_confidence_adjusted_evidence = (
    fuse_confidence_adjusted_evidence
)
sys.modules["cidar_confidence_fusion"] = (
    fusion_module
)
# ---------------------------------------------------------------------------
# CIDAR audit record
# ---------------------------------------------------------------------------
def create_audit_record(
    weights,
    criteria,
    threshold=0.70,
):
    """
    Create a deterministic CIDAR audit record.
    The weighted score is rounded to two decimal places so that
    values such as 0.8300000000000001 are represented as 0.83.
    """
    score = weighted_score(
        weights,
        criteria,
    )
    return {
        "weights": list(weights),
        "criteria": list(criteria),
        "weighted_score": round(score, 2),
        "threshold": round(
            float(threshold),
            2,
        ),
        "decision": ethical_decision(
            weights=weights,
            criteria=criteria,
            threshold=threshold,
        ),
    }
audit_module = types.ModuleType(
    "cidar_audit"
)
audit_module.create_audit_record = (
    create_audit_record
)
sys.modules["cidar_audit"] = (
    audit_module
)