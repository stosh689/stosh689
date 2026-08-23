"""
Ethical decision-making utilities for GEDT/CIDAR.
"""


def ethical_decision(weights, criteria, threshold=0.70):
    """
    Calculate a weighted ethical decision.

    Returns:
        "Approved" when the weighted score meets the threshold.
        "Review" otherwise.
    """

    if len(weights) != len(criteria):
        raise ValueError(
            "weights and criteria must have the same length"
        )

    if not weights:
        raise ValueError(
            "weights and criteria cannot be empty"
        )

    total_weight = sum(float(weight) for weight in weights)

    if total_weight <= 0:
        raise ValueError(
            "total weight must be greater than zero"
        )

    score = sum(
        float(weight) * float(criterion)
        for weight, criterion in zip(weights, criteria)
    ) / total_weight

    return "Approved" if score >= threshold else "Review"