"""
CIDAR camera geometry utilities.

Converts image-plane coordinates and depth measurements into
3D camera-frame coordinates using a pinhole camera model.

Supports:
- pixel -> camera coordinates
- camera coordinates -> pixel coordinates
- batch projection
- Euclidean range
- field-of-view calculations

Python >= 3.10
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan, degrees, isfinite, sqrt, tan
from typing import Iterable

from .cidar_range import euclidean_range


@dataclass(frozen=True)
class CameraIntrinsics:
    """Pinhole camera intrinsic parameters."""

    fx: float
    fy: float
    cx: float
    cy: float
    width: int | None = None
    height: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("fx", self.fx),
            ("fy", self.fy),
            ("cx", self.cx),
            ("cy", self.cy),
        ):
            value = float(value)

            if not isfinite(value):
                raise ValueError(
                    f"{name} must be finite"
                )

        if self.fx <= 0:
            raise ValueError("fx must be positive")

        if self.fy <= 0:
            raise ValueError("fy must be positive")

        if self.width is not None and self.width <= 0:
            raise ValueError("width must be positive")

        if self.height is not None and self.height <= 0:
            raise ValueError("height must be positive")


@dataclass(frozen=True)
class CameraPoint:
    """A point expressed in camera coordinates."""

    x: float
    y: float
    z: float

    @property
    def range(self) -> float:
        """Return Euclidean distance from the camera origin."""
        return euclidean_range(
            self.x,
            self.y,
            self.z,
        )


@dataclass(frozen=True)
class PixelPoint:
    """A point expressed in image coordinates."""

    u: float
    v: float


def validate_pixel(
    u: float,
    v: float,
    intrinsics: CameraIntrinsics,
) -> bool:
    """Return whether a pixel lies inside the image bounds."""
    if intrinsics.width is None:
        return True

    if intrinsics.height is None:
        return True

    return (
        0 <= u < intrinsics.width
        and 0 <= v < intrinsics.height
    )


def pixel_to_camera(
    u: float,
    v: float,
    depth: float,
    intrinsics: CameraIntrinsics,
) -> CameraPoint:
    """
    Convert pixel coordinates and depth into camera coordinates.

    Pinhole model:

        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy
        Z = depth
    """
    u = float(u)
    v = float(v)
    depth = float(depth)

    if not all(
        isfinite(value)
        for value in (u, v, depth)
    ):
        raise ValueError(
            "u, v, and depth must be finite"
        )

    if depth <= 0:
        raise ValueError(
            "depth must be positive"
        )

    return CameraPoint(
        x=(u - intrinsics.cx)
        * depth
        / intrinsics.fx,
        y=(v - intrinsics.cy)
        * depth
        / intrinsics.fy,
        z=depth,
    )


def camera_to_pixel(
    point: CameraPoint,
    intrinsics: CameraIntrinsics,
) -> PixelPoint:
    """
    Project a camera-frame 3D point into image coordinates.
    """
    if point.z <= 0:
        raise ValueError(
            "point must be in front of the camera"
        )

    u = (
        intrinsics.fx
        * point.x
        / point.z
        + intrinsics.cx
    )

    v = (
        intrinsics.fy
        * point.y
        / point.z
        + intrinsics.cy
    )

    return PixelPoint(
        u=u,
        v=v,
    )


def pixels_to_camera_points(
    observations: Iterable[
        tuple[float, float, float]
    ],
    intrinsics: CameraIntrinsics,
) -> tuple[CameraPoint, ...]:
    """Convert multiple pixel/depth observations."""
    return tuple(
        pixel_to_camera(
            u,
            v,
            depth,
            intrinsics,
        )
        for u, v, depth in observations
    )


def camera_points_to_pixels(
    points: Iterable[CameraPoint],
    intrinsics: CameraIntrinsics,
) -> tuple[PixelPoint, ...]:
    """Project multiple camera-frame points."""
    return tuple(
        camera_to_pixel(
            point,
            intrinsics,
        )
        for point in points
    )


def horizontal_fov(
    intrinsics: CameraIntrinsics,
) -> float:
    """Return horizontal field of view in degrees."""
    if intrinsics.width is None:
        raise ValueError(
            "camera width is required"
        )

    return degrees(
        2.0
        * atan(
            intrinsics.width
            / (2.0 * intrinsics.fx)
        )
    )


def vertical_fov(
    intrinsics: CameraIntrinsics,
) -> float:
    """Return vertical field of view in degrees."""
    if intrinsics.height is None:
        raise ValueError(
            "camera height is required"
        )

    return degrees(
        2.0
        * atan(
            intrinsics.height
            / (2.0 * intrinsics.fy)
        )
    )


def viewing_angle(
    u: float,
    v: float,
    intrinsics: CameraIntrinsics,
) -> tuple[float, float]:
    """
    Return horizontal and vertical viewing angles in degrees.
    """
    horizontal = degrees(
        atan(
            (float(u) - intrinsics.cx)
            / intrinsics.fx
        )
    )

    vertical = degrees(
        atan(
            (float(v) - intrinsics.cy)
            / intrinsics.fy
        )
    )

    return horizontal, vertical


def ray_direction(
    u: float,
    v: float,
    intrinsics: CameraIntrinsics,
) -> tuple[float, float, float]:
    """
    Return a normalized camera ray through a pixel.
    """
    x = (
        float(u) - intrinsics.cx
    ) / intrinsics.fx

    y = (
        float(v) - intrinsics.cy
    ) / intrinsics.fy

    z = 1.0

    magnitude = sqrt(
        x * x
        + y * y
        + z * z
    )

    return (
        x / magnitude,
        y / magnitude,
        z / magnitude,
    )


__all__ = [
    "CameraIntrinsics",
    "CameraPoint",
    "PixelPoint",
    "camera_to_pixel",
    "horizontal_fov",
    "pixel_to_camera",
    "pixels_to_camera_points",
    "camera_points_to_pixels",
    "ray_direction",
    "validate_pixel",
    "vertical_fov",
    "viewing_angle",
]