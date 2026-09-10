"""GEDT v11 configuration system.

Provides a small, dependency-free configuration layer for
reproducible economic digital-twin experiments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GEDTConfig:
    """Configuration for a GEDT experiment."""

    version: str = "11.0.0"
    periods: int = 12
    trials: int = 1000
    seed: int = 42

    initial_gdp: float = 1000.0
    initial_inflation: float = 0.02
    initial_unemployment: float = 0.05

    demand_shock: float = 0.0
    supply_shock: float = 0.0
    policy_rate_change: float = 0.0

    def validate(self) -> "GEDTConfig":
        """Validate configuration values."""

        if self.periods < 1:
            raise ValueError("periods must be at least 1")

        if self.trials < 1:
            raise ValueError("trials must be at least 1")

        if self.initial_gdp <= 0:
            raise ValueError("initial_gdp must be greater than zero")

        if self.initial_inflation <= -1:
            raise ValueError("initial_inflation is out of range")

        if self.initial_unemployment < 0:
            raise ValueError("initial_unemployment cannot be negative")

        return self

    def to_dict(self) -> dict[str, Any]:
        """Return configuration as a dictionary."""

        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize configuration to JSON."""

        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )

    def save(self, path: str | Path) -> Path:
        """Save configuration to a JSON file."""

        self.validate()

        output_path = Path(path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_json() + "\n",
            encoding="utf-8",
        )

        return output_path

    @classmethod
    def from_dict(
        cls,
        values: dict[str, Any],
    ) -> "GEDTConfig":
        """Create configuration from a dictionary."""

        config = cls(**values)
        config.validate()
        return config

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "GEDTConfig":
        """Load configuration from JSON."""

        input_path = Path(path)

        values = json.loads(
            input_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(values, dict):
            raise ValueError(
                "configuration file must contain a JSON object"
            )

        return cls.from_dict(values)


DEFAULT_CONFIG = GEDTConfig()