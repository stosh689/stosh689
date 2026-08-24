def confidence_adjusted_score(score, confidence):
    """Adjust a sensor score according to confidence."""

    if not 0.0 <= score <= 1.0:
        raise ValueError("Score must be between 0 and 1.")

    if not 0.0 <= confidence <= 1.0:
        raise ValueError("Confidence must be between 0 and 1.")

    return round(score * confidence, 10)