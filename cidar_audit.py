from ethical_decision import ethical_decision


def create_audit_record(weights, criteria, threshold=0.70):
    """Create a transparent record of an ethical decision."""

    decision = ethical_decision(
        weights=weights,
        criteria=criteria,
        threshold=threshold,
    )

    total_weight = sum(weights)
    weighted_score = sum(
        weight * criterion
        for weight, criterion in zip(weights, criteria)
    ) / total_weight

    return {
        "weights": list(weights),
        "criteria": list(criteria),
        "weighted_score": weighted_score,
        "threshold": threshold,
        "decision": decision,
    }