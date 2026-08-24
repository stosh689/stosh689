"""
CIDAR Outlier Rejection

Robust range-measurement filtering using the median
and median absolute deviation (MAD).
"""


def reject_outliers(ranges, threshold=3.5):
    """
    Return valid range measurements with statistical outliers removed.

    Parameters
    ----------
    ranges : iterable of numbers
        Range measurements.
    threshold : float
        Modified z-score threshold.

    Returns
    -------
    list[float]
        Filtered measurements.
    """

    if ranges is None:
        raise ValueError("ranges cannot be None")

    values = [float(value) for value in ranges]

    if not values:
        raise ValueError("ranges cannot be empty")

    if threshold <= 0:
        raise ValueError("threshold must be greater than zero")

    if any(value < 0 for value in values):
        raise ValueError("range measurements cannot be negative")

    # Very small datasets cannot support reliable outlier detection.
    if len(values) < 3:
        return values.copy()

    ordered = sorted(values)
    middle = len(ordered) // 2

    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2.0

    deviations = [abs(value - median) for value in values]
    ordered_deviations = sorted(deviations)

    middle = len(ordered_deviations) // 2

    if len(ordered_deviations) % 2:
        mad = ordered_deviations[middle]
    else:
        mad = (
            ordered_deviations[middle - 1]
            + ordered_deviations[middle]
        ) / 2.0

    # If all measurements are effectively identical,
    # there are no detectable outliers.
    if mad == 0:
        return [
            value
            for value in values
            if value == median
        ]

    filtered = []

    for value in values:
        modified_z_score = (
            0.6745 * abs(value - median) / mad
        )

        if modified_z_score <= threshold:
            filtered.append(value)

    # Never silently discard every measurement.
    if not filtered:
        return [median]

    return filtered


if __name__ == "__main__":
    measurements = [100.0, 101.0, 102.0, 450.0]

    result = reject_outliers(measurements)

    print("Input:", measurements)
    print("Filtered:", result)