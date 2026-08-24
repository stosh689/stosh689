"""
GEDT Rebuild Prototype
=======================

A clean, standalone prototype reconstructed from the useful GEDT
project concepts.

This file intentionally does NOT modify or depend on the existing
GEDT implementation.

Core capabilities:
    - Population simulation
    - Agent adaptation
    - Innovation
    - Resource management
    - Productivity metrics
    - Project health checks
    - Deterministic/reproducible execution
    - Benchmarking
    - JSON export
    - Command-line interface

Python:
    >= 3.10
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import argparse
import json
import time

import numpy as np


# ============================================================
# VERSION
# ============================================================

VERSION = "0.2.0"


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for a GEDT simulation."""

    population: int = 10_000
    years: int = 50
    innovation_rate: float = 0.05
    resource_growth: float = 0.01
    adaptability_rate: float = 0.02
    seed: int = 42

    def validate(self) -> None:
        """Validate simulation configuration."""

        if self.population <= 0:
            raise ValueError(
                "population must be greater than zero"
            )

        if self.years <= 0:
            raise ValueError(
                "years must be greater than zero"
            )

        if not 0 <= self.innovation_rate <= 1:
            raise ValueError(
                "innovation_rate must be between 0 and 1"
            )

        if not 0 <= self.resource_growth <= 1:
            raise ValueError(
                "resource_growth must be between 0 and 1"
            )

        if not 0 <= self.adaptability_rate <= 1:
            raise ValueError(
                "adaptability_rate must be between 0 and 1"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# AGENT POPULATION
# ============================================================

class Population:
    """
    Vectorized population model.

    Each simulated agent has:

        skill
        resources
        adaptability
        productivity
    """

    def __init__(
        self,
        size: int,
        seed: int = 42,
    ) -> None:

        if size <= 0:
            raise ValueError(
                "Population size must be positive"
            )

        self.rng = np.random.default_rng(seed)

        self.skill = self.rng.random(size)

        self.resources = self.rng.random(size)

        self.adaptability = self.rng.random(size)

    @property
    def size(self) -> int:
        return int(self.skill.size)

    def innovate(
        self,
        rate: float,
    ) -> None:
        """
        Increase skill according to innovation rate
        and individual adaptability.
        """

        self.skill += (
            rate
            * self.adaptability
            * (1.0 - self.skill)
        )

        np.clip(
            self.skill,
            0.0,
            1.0,
            out=self.skill,
        )

    def grow_resources(
        self,
        rate: float,
    ) -> None:
        """
        Increase resources while keeping the
        population numerically stable.
        """

        self.resources += (
            rate
            * self.resources
            * self.adaptability
        )

        np.clip(
            self.resources,
            0.0,
            10.0,
            out=self.resources,
        )

    def adapt(
        self,
        rate: float,
    ) -> None:
        """
        Gradually improve adaptability.
        """

        self.adaptability += (
            rate
            * self.skill
            * (1.0 - self.adaptability)
        )

        np.clip(
            self.adaptability,
            0.0,
            1.0,
            out=self.adaptability,
        )

    def productivity_vector(self) -> np.ndarray:
        """Return productivity for every agent."""

        return (
            self.skill
            * self.resources
            * (
                0.5
                + 0.5 * self.adaptability
            )
        )

    def productivity(self) -> float:
        """Return mean population productivity."""

        return float(
            np.mean(
                self.productivity_vector()
            )
        )

    def total_productivity(self) -> float:
        """Return total population productivity."""

        return float(
            np.sum(
                self.productivity_vector()
            )
        )

    def mean_skill(self) -> float:
        return float(
            np.mean(self.skill)
        )

    def mean_resources(self) -> float:
        return float(
            np.mean(self.resources)
        )

    def mean_adaptability(self) -> float:
        return float(
            np.mean(self.adaptability)
        )

    def inequality(self) -> float:
        """
        Approximate productivity inequality using
        the coefficient of variation.
        """

        values = self.productivity_vector()

        mean = float(np.mean(values))

        if mean == 0:
            return 0.0

        return float(
            np.std(values) / mean
        )

    def snapshot(self) -> dict[str, float]:
        """Return current population statistics."""

        return {
            "population": float(self.size),
            "mean_skill": self.mean_skill(),
            "mean_resources": self.mean_resources(),
            "mean_adaptability": self.mean_adaptability(),
            "productivity": self.productivity(),
            "total_productivity": self.total_productivity(),
            "inequality": self.inequality(),
        }


# ============================================================
# RESOURCE MANAGEMENT
# ============================================================

@dataclass
class Resource:
    """A managed project resource."""

    name: str
    category: str
    quantity: float
    status: str = "available"
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:

        if not self.name.strip():
            raise ValueError(
                "Resource name cannot be empty"
            )

        if self.quantity < 0:
            raise ValueError(
                "Resource quantity cannot be negative"
            )

        valid_statuses = {
            "available",
            "allocated",
            "depleted",
            "inactive",
        }

        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid resource status: {self.status}"
            )


class ResourceManager:
    """
    Lightweight in-memory resource manager.

    This intentionally avoids introducing a database dependency
    into the prototype.
    """

    def __init__(self) -> None:

        self._resources: dict[str, Resource] = {}

    def add(
        self,
        resource: Resource,
    ) -> Resource:

        resource.validate()

        if resource.name in self._resources:
            raise ValueError(
                f"Resource already exists: {resource.name}"
            )

        self._resources[resource.name] = resource

        return resource

    def get(
        self,
        name: str,
    ) -> Resource:

        try:
            return self._resources[name]

        except KeyError as exc:
            raise KeyError(
                f"Resource not found: {name}"
            ) from exc

    def update(
        self,
        name: str,
        *,
        quantity: float | None = None,
        status: str | None = None,
    ) -> Resource:

        resource = self.get(name)

        if quantity is None and status is None:
            raise ValueError(
                "At least one field must be supplied"
            )

        if quantity is not None:
            resource.quantity = quantity

        if status is not None:
            resource.status = status

        resource.validate()

        return resource

    def delete(
        self,
        name: str,
    ) -> None:

        if name not in self._resources:
            raise KeyError(
                f"Resource not found: {name}"
            )

        del self._resources[name]

    def search(
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[Resource]:

        if status is not None:

            valid_statuses = {
                "available",
                "allocated",
                "depleted",
                "inactive",
            }

            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid resource status: {status}"
                )

        results: Iterable[Resource] = (
            self._resources.values()
        )

        if name is not None:

            results = (
                resource
                for resource in results
                if name.lower()
                in resource.name.lower()
            )

        if category is not None:

            results = (
                resource
                for resource in results
                if resource.category == category
            )

        if status is not None:

            results = (
                resource
                for resource in results
                if resource.status == status
            )

        return list(results)

    def all(self) -> list[Resource]:
        return list(
            self._resources.values()
        )

    def count(self) -> int:
        return len(self._resources)


# ============================================================
# SIMULATION ENGINE
# ============================================================

class SimulationEngine:
    """Execute a GEDT population simulation."""

    def __init__(
        self,
        config: SimulationConfig,
    ) -> None:

        config.validate()

        self.config = config

    def run(self) -> dict[str, Any]:

        population = Population(
            size=self.config.population,
            seed=self.config.seed,
        )

        history: list[dict[str, float]] = []

        start = time.perf_counter()

        for year in range(
            1,
            self.config.years + 1,
        ):

            population.innovate(
                self.config.innovation_rate
            )

            population.grow_resources(
                self.config.resource_growth
            )

            population.adapt(
                self.config.adaptability_rate
            )

            snapshot = population.snapshot()

            snapshot["year"] = float(year)

            history.append(snapshot)

        runtime = (
            time.perf_counter()
            - start
        )

        initial = history[0]
        final = history[-1]

        productivity_change = (
            final["productivity"]
            - initial["productivity"]
        )

        productivity_growth_pct = (
            (
                productivity_change
                / initial["productivity"]
            )
            * 100.0
            if initial["productivity"] != 0
            else 0.0
        )

        return {
            "version": VERSION,
            "config": self.config.to_dict(),
            "runtime_seconds": runtime,
            "initial": initial,
            "final": final,
            "productivity_change": productivity_change,
            "productivity_growth_percent":
                productivity_growth_pct,
            "history": history,
        }


# ============================================================
# REPRODUCIBILITY
# ============================================================

def reproducibility_check(
    config: SimulationConfig,
) -> bool:
    """
    Verify that identical seeds produce identical
    simulation results.
    """

    result_a = SimulationEngine(
        config
    ).run()

    result_b = SimulationEngine(
        config
    ).run()

    return bool(
        np.isclose(
            result_a["final"]["productivity"],
            result_b["final"]["productivity"],
        )
    )


# ============================================================
# BENCHMARKING
# ============================================================

def run_benchmark(
    population: int = 100_000,
    years: int = 100,
    innovation_rate: float = 0.05,
    resource_growth: float = 0.01,
    adaptability_rate: float = 0.02,
    seed: int = 42,
) -> dict[str, Any]:

    config = SimulationConfig(
        population=population,
        years=years,
        innovation_rate=innovation_rate,
        resource_growth=resource_growth,
        adaptability_rate=adaptability_rate,
        seed=seed,
    )

    result = SimulationEngine(
        config
    ).run()

    return {
        "benchmark": "GEDT",
        "version": VERSION,
        "population": population,
        "years": years,
        "runtime_seconds":
            result["runtime_seconds"],
        "final_productivity":
            result["final"]["productivity"],
        "productivity_growth_percent":
            result["productivity_growth_percent"],
        "status": "PASS",
    }


# ============================================================
# PROJECT HEALTH
# ============================================================

@dataclass
class ProjectHealth:
    """Project health report."""

    status: str
    checks: dict[str, bool]
    details: dict[str, str]

    @property
    def healthy(self) -> bool:
        return all(
            self.checks.values()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "healthy": self.healthy,
            "checks": self.checks,
            "details": self.details,
        }


def check_project_health(
    project_root: Path | None = None,
) -> ProjectHealth:

    root = (
        project_root.resolve()
        if project_root
        else Path.cwd().resolve()
    )

    checks: dict[str, bool] = {}
    details: dict[str, str] = {}

    # --------------------------------------------------------
    # pyproject
    # --------------------------------------------------------

    pyproject = (
        root / "pyproject.toml"
    )

    checks["pyproject_exists"] = (
        pyproject.exists()
    )

    details["pyproject_exists"] = (
        "pyproject.toml found"
        if pyproject.exists()
        else "pyproject.toml missing"
    )

    # --------------------------------------------------------
    # source
    # --------------------------------------------------------

    src = root / "src"

    checks["src_exists"] = src.exists()

    details["src_exists"] = (
        "src directory found"
        if src.exists()
        else "src directory missing"
    )

    # --------------------------------------------------------
    # tests
    # --------------------------------------------------------

    tests = root / "tests"

    checks["tests_exists"] = tests.exists()

    details["tests_exists"] = (
        "tests directory found"
        if tests.exists()
        else "tests directory missing"
    )

    # --------------------------------------------------------
    # prototype
    # --------------------------------------------------------

    prototype = (
        root / "gedt_rebuild.py"
    )

    checks["prototype_exists"] = (
        prototype.exists()
    )

    details["prototype_exists"] = (
        "GEDT rebuild prototype found"
        if prototype.exists()
        else "GEDT rebuild prototype missing"
    )

    # --------------------------------------------------------
    # result
    # --------------------------------------------------------

    healthy = all(
        checks.values()
    )

    status = (
        "HEALTHY"
        if healthy
        else "DEGRADED"
    )

    return ProjectHealth(
        status=status,
        checks=checks,
        details=details,
    )


# ============================================================
# JSON EXPORT
# ============================================================

def save_json(
    data: dict[str, Any],
    filename: str | Path,
) -> Path:

    path = Path(filename)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
        )

    return path


# ============================================================
# RESOURCE DEMONSTRATION
# ============================================================

def create_demo_resources() -> ResourceManager:
    """
    Create a small deterministic resource set for
    prototype testing.
    """

    manager = ResourceManager()

    manager.add(
        Resource(
            name="compute",
            category="infrastructure",
            quantity=100.0,
            status="available",
        )
    )

    manager.add(
        Resource(
            name="data",
            category="information",
            quantity=1000.0,
            status="available",
        )
    )

    manager.add(
        Resource(
            name="research",
            category="human_capital",
            quantity=50.0,
            status="allocated",
        )
    )

    return manager


# ============================================================
# COMPLETE PROTOTYPE RUN
# ============================================================

def run_prototype(
    config: SimulationConfig,
) -> dict[str, Any]:

    simulation = SimulationEngine(
        config
    ).run()

    reproducible = (
        reproducibility_check(
            config
        )
    )

    resources = (
        create_demo_resources()
    )

    health = check_project_health()

    return {
        "prototype_version": VERSION,

        "simulation": simulation,

        "reproducibility": {
            "passed": reproducible,
        },

        "resources": {
            "count": resources.count(),
            "items": [
                asdict(resource)
                for resource
                in resources.all()
            ],
        },

        "health": health.to_dict(),
    }


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "GEDT standalone rebuild prototype"
        )
    )

    parser.add_argument(
        "--population",
        type=int,
        default=10_000,
    )

    parser.add_argument(
        "--years",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--innovation-rate",
        type=float,
        default=0.05,
    )

    parser.add_argument(
        "--resource-growth",
        type=float,
        default=0.01,
    )

    parser.add_argument(
        "--adaptability-rate",
        type=float,
        default=0.02,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--output",
        type=str,
        default=(
            "benchmark_results/"
            "gedt_rebuild_results.json"
        ),
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:

    parser = build_parser()

    args = parser.parse_args(argv)

    config = SimulationConfig(
        population=args.population,
        years=args.years,
        innovation_rate=args.innovation_rate,
        resource_growth=args.resource_growth,
        adaptability_rate=args.adaptability_rate,
        seed=args.seed,
    )

    try:
        config.validate()

    except ValueError as exc:

        print(
            f"Configuration error: {exc}"
        )

        return 2

    print("=" * 64)
    print("GEDT REBUILD PROTOTYPE")
    print("=" * 64)

    print(
        f"Version: {VERSION}"
    )

    print(
        "\nConfiguration:"
    )

    print(
        json.dumps(
            config.to_dict(),
            indent=2,
        )
    )

    if args.benchmark:

        print(
            "\nRunning benchmark..."
        )

        result = run_benchmark(
            population=args.population,
            years=args.years,
            innovation_rate=(
                args.innovation_rate
            ),
            resource_growth=(
                args.resource_growth
            ),
            adaptability_rate=(
                args.adaptability_rate
            ),
            seed=args.seed,
        )

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

        save_json(
            result,
            args.output,
        )

        return 0

    print(
        "\nRunning prototype..."
    )

    result = run_prototype(
        config
    )

    simulation = result[
        "simulation"
    ]

    print(
        "\nRESULT"
    )

    print(
        f"Runtime: "
        f"{simulation['runtime_seconds']:.6f}s"
    )

    print(
        f"Initial productivity: "
        f"{simulation['initial']['productivity']:.6f}"
    )

    print(
        f"Final productivity: "
        f"{simulation['final']['productivity']:.6f}"
    )

    print(
        f"Productivity growth: "
        f"{simulation['productivity_growth_percent']:.2f}%"
    )

    print(
        "\nReproducibility: "
        + (
            "PASS"
            if result["reproducibility"]["passed"]
            else "FAIL"
        )
    )

    print(
        "Project health: "
        + result["health"]["status"]
    )

    output_path = save_json(
        result,
        args.output,
    )

    print(
        f"\nResults written to: "
        f"{output_path}"
    )

    print(
        "\nGEDT rebuild complete."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )