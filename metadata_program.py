"""Standalone GEDT metadata model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GEDTMetadata:
    name: str
    version: str
    description: str
    python_requires: str
    dependencies: tuple[str, ...]


def get_metadata() -> GEDTMetadata:
    return GEDTMetadata(
        name="gedt",
        version="0.1.0",
        description="Global Economic Digital Twin",
        python_requires=">=3.10",
        dependencies=("pytest",),
    )


if __name__ == "__main__":
    print(get_metadata())