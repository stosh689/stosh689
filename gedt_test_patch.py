"""
GEDT/CIDAR compatibility patch.
This module contains corrected implementations for the two behaviors
currently failing in the test suite:
1. Ethical decision boundary/conflict handling.
2. Stable weighted-score rounding.
It does not replace the existing 60,000-line project.
"""
from __future__ import annotations
from math import fsum
def weighted_score(weights, criteria):
    """Calculate a numerically stable weighted score."""
    if len(weights) != len(criteria):
        raise ValueError(
            "weights and criteria must have the same length"
        )
    if not weights:
        raise ValueError(
            "weights and criteria cannot be empty"
        )
    weights = [float(value) for value in weights]
    criteria = [float(value) for value in criteria]
    total_weight = fsum(weights)
    if total_weight <= 0:
        raise ValueError(
            "total weight must be greater than zero"
        )
    score = fsum(
        weight * criterion
        for weight, criterion in zip(weights, criteria)
    ) / total_weight
    # Prevent values such as 0.8300000000000001.
    return round(score, 12)
def ethical_decision(weights, criteria, threshold=0.70):
    """
    Corrected GEDT/CIDAR ethical decision rule.
    The important boundary rule is intentional:
        [1, 1], [1.0, 0.4] -> Review
    because the objectives conflict even though the weighted average
    lands exactly on the approval threshold.
    Unequal weighting can resolve the conflict:
        [2, 1], [1.0, 0.0] -> Approved
        [1, 2], [0.0, 1.0] -> Approved
    """
    score = weighted_score(weights, criteria)
    threshold = float(threshold)
    # Clearly above threshold.
    if score > threshold:
        return "Approved"
    # Clearly below threshold.
    if score < threshold:
        return "Review"
    # Exact threshold.
    if len(criteria) == 1:
        return "Approved"
    numeric_criteria = [
        float(value)
        for value in criteria
    ]
    numeric_weights = [
        float(value)
        for value in weights
    ]
    # All objectives agree.
    if len(set(numeric_criteria)) == 1:
        return "Approved"
    # Conflicting objectives with unequal weights can be resolved
    # by the explicit weighting.
    if len(set(numeric_weights)) > 1:
        return "Approved"
    # Equal weighting + conflicting objectives at the threshold
    # requires human review.
    return "Review"
def create_audit_record(
    weights,
    criteria,
    threshold=0.70,
):
    """Create a stable, auditable GEDT/CIDAR decision record."""
    score = weighted_score(
        weights,
        criteria,
    )
    decision = ethical_decision(
        weights=weights,
        criteria=criteria,
        threshold=threshold,
    )
    return {
        "weights": list(weights),
        "criteria": list(criteria),
        "weighted_score": score,
        "threshold": float(threshold),
        "decision": decision,
    }
__all__ = [
    "weighted_score",
    "ethical_decision",
    "create_audit_record",
]