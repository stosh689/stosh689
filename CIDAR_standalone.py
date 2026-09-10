"""
CIDAR Standalone
Camera + LiDAR + Radar sensor fusion

Python 3.9+
Standard library only.
"""

import math
import random


def fuse(camera, lidar, radar):
    """Fuse three depth measurements using inverse-variance weighting."""

    measurements = [
        (camera, 2.0),
        (lidar, 0.2),
        (radar, 1.0),
    ]

    weights = []

    for value, sigma in measurements:
        weight = 1.0 / (sigma * sigma)
        weights.append((value, weight))

    total_weight = sum(weight for _, weight in weights)

    estimate = sum(
        value * weight
        for value, weight in weights
    ) / total_weight

    uncertainty = math.sqrt(1.0 / total_weight)

    return estimate, uncertainty


def main():
    random.seed(42)

    true_depth = 20.0

    camera = random.gauss(true_depth, 2.0)
    lidar = random.gauss(true_depth, 0.2)
    radar = random.gauss(true_depth, 1.0)

    estimate, uncertainty = fuse(
        camera,
        lidar,
        radar,
    )

    print("=" * 50)
    print("CIDAR STANDALONE")
    print("=" * 50)

    print(f"True depth:   {true_depth:.3f} m")
    print(f"Camera:       {camera:.3f} m")
    print(f"LiDAR:        {lidar:.3f} m")
    print(f"Radar:        {radar:.3f} m")

    print("-" * 50)

    print(f"Fused depth:  {estimate:.3f} m")
    print(f"Uncertainty:  ±{uncertainty:.3f} m")

    error = abs(estimate - true_depth)

    print(f"Error:        {error:.3f} m")

    print("-" * 50)

    if error <= 1.0:
        print("STATUS: PASS")
    else:
        print("STATUS: REVIEW")

    print("=" * 50)


if __name__ == "__main__":
    main()