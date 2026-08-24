from __future__ import annotations

from ethical_decision import ethical_decision


def create_audit_record(
    weights,
    criteria,
    threshold=0.70,
):
    """Create a transparent, reproducible record of an ethical decision."""

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

    weighted_score = round(
        sum(
            float(weight) * float(criterion)
            for weight, criterion in zip(weights, criteria)
        ) / total_weight,
        2,
    )

    decision = ethical_decision(
        weights=weights,
        criteria=criteria,
        threshold=threshold,
    )

    return {
        "weights": list(weights),
        "criteria": list(criteria),
        "weighted_score": weighted_score,
        "threshold": float(threshold),
        "decision": decision,
    }


if __name__ == "__main__":
    record = create_audit_record(
        weights=[5, 3, 2],
        criteria=[0.9, 0.8, 0.7],
        threshold=0.70,
    )

    print("CIDAR AUDIT")
    print("=" * 40)

    for key, value in record.items():
        print(f"{key}: {value}")