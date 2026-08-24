"""
GEDT Rebuild Prototype
=======================

Clean standalone prototype reconstructed from the useful GEDT design
material currently embedded in pyproject.toml.

Features:
- deterministic agent population
- vectorized NumPy simulation
- innovation/adaptation model
- productivity measurement
- simulation history
- performance measurement
- project health reporting
- JSON serialization
- command-line execution

Python >= 3.10
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time
from typing import Any

import numpy as np


# ============================================================
# Configuration
# ============================================================

@dataclass(frozen=True)
class SimulationConfig:
    population: int = 10_000
    years: int = 50
    innovation_rate: float = 0.05
    seed: int = 42

    def validate(self) -> None:
        if self.population <= 0:
            raise ValueError("population must be greater than zero")

        if self.years <= 0:
            raise ValueError("years must be greater than zero")

        if not 0 <= self.innovation_rate <= 1:
            raise ValueError(
                "innovation_rate must be between 0 and 1"
            )


# ============================================================
# Population Model
# ============================================================

class Population:
    """
    Vectorized population of simulated agents.

    Each agent has:
        skill
        resources
        adaptability
    """

    def __init__(
        self,
        size: int,
        seed: int = 42,
    ) -> None:

        if size <= 0:
            raise ValueError("Population size must be positive")

        rng = np.random.default_rng(seed)

        self.skill = rng.random(size)
        self.resources = rng.random(size)
        self.adaptability = rng.random(size)

    @property
    def size(self) -> int:
        return len(self.skill)

    def innovate(self, rate: float) -> None:
        """
        Apply innovation according to agent adaptability.
        """

        if not 0 <= rate <= 1:
            raise ValueError(
                "Innovation rate must be between 0 and 1"
            )

        self.skill += rate * self.adaptability

        np.clip(
            self.skill,
            0.0,
            1.0,
            out=self.skill,
        )

    def productivity(self) -> float:
        """
        Calculate mean population productivity.
        """

        return float(
            np.mean(
                self.skill * self.resources
            )
        )

    def mean_skill(self) -> float:
        return float(np.mean(self.skill))

    def mean_resources(self) -> float:
        return float(np.mean(self.resources))

    def mean_adaptability(self) -> float:
        return float(np.mean(self.adaptability))


# ============================================================
# Simulation Engine
# ============================================================

class SimulationEngine:
    """
    Main GEDT simulation engine.
    """

    def run(
        self,
        config: SimulationConfig,
    ) -> dict[str, Any]:

        config.validate()

        population = Population(
            size=config.population,
            seed=config.seed,
        )

        history: list[float] = []
        skill_history: list[float] = []
        resource_history: list[float] = []

        for _year in range(config.years):

            population.innovate(
                config.innovation_rate
            )

            history.append(
                population.productivity()
            )

            skill_history.append(
                population.mean_skill()
            )

            resource_history.append(
                population.mean_resources()
            )

        return {
            "config": asdict(config),
            "population": population.size,
            "years": config.years,
            "final_productivity": history[-1],
            "initial_productivity": history[0],
            "productivity_change": (
                history[-1] - history[0]
            ),
            "history": history,
            "skill_history": skill_history,
            "resource_history": resource_history,
        }


# ============================================================
# Performance
# ============================================================

class Profiler:
    """
    Simple execution profiler.
    """

    @staticmethod
    def measure(
        function,
        *args,
        **kwargs,
    ) -> dict[str, Any]:

        start = time.perf_counter()

        result = function(
            *args,
            **kwargs,
        )

        elapsed = time.perf_counter() - start

        return {
            "result": result,
            "runtime_seconds": elapsed,
        }


# ============================================================
# Health System
# ============================================================

@dataclass
class ProjectHealth:
    status: str
    checks: dict[str, bool]
    details: dict[str, str]

    @property
    def healthy(self) -> bool:
        return all(self.checks.values())


def check_project_health(
    project_root: Path | None = None,
) -> ProjectHealth:

    root = (
        project_root
        if project_root is not None
        else Path.cwd()
    )

    checks: dict[str, bool] = {}
    details: dict[str, str] = {}

    pyproject = root / "pyproject.toml"

    checks["pyproject_exists"] = pyproject.exists()

    details["pyproject_exists"] = (
        "pyproject.toml found"
        if pyproject.exists()
        else "pyproject.toml missing"
    )

    src = root / "src"

    checks["src_exists"] = src.exists()

    details["src_exists"] = (
        "src directory found"
        if src.exists()
        else "src directory missing"
    )

    tests = root / "tests"

    checks["tests_exist"] = tests.exists()

    details["tests_exist"] = (
        "tests directory found"
        if tests.exists()
        else "tests directory missing"
    )

    status = (
        "HEALTHY"
        if all(checks.values())
        else "DEGRADED"
    )

    return ProjectHealth(
        status=status,
        checks=checks,
        details=details,
    )


# ============================================================
# Benchmark
# ============================================================

def run_benchmark(
    population: int = 100_000,
    years: int = 100,
    innovation_rate: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:

    config = SimulationConfig(
        population=population,
        years=years,
        innovation_rate=innovation_rate,
        seed=seed,
    )

    profiler = Profiler()

    measured = profiler.measure(
        SimulationEngine().run,
        config,
    )

    result = measured["result"]

    return {
        "experiment": "gedt_vectorized_benchmark",
        "population": population,
        "years": years,
        "innovation_rate": innovation_rate,
        "runtime_seconds": measured[
            "runtime_seconds"
        ],
        "final_productivity": result[
            "final_productivity"
        ],
        "productivity_change": result[
            "productivity_change"
        ],
        "status": "PASS",
    }


# ============================================================
# Reproducibility
# ============================================================

def reproducibility_check() -> bool:

    config = SimulationConfig(
        population=5_000,
        years=50,
        innovation_rate=0.05,
        seed=42,
    )

    engine = SimulationEngine()

    result_a = engine.run(config)
    result_b = engine.run(config)

    return bool(
        np.isclose(
            result_a["final_productivity"],
            result_b["final_productivity"],
        )
    )


# ============================================================
# JSON Utilities
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
# Main Prototype
# ============================================================

def main() -> None:

    print("=" * 60)
    print("GEDT REBUILD PROTOTYPE")
    print("=" * 60)

    config = SimulationConfig(
        population=10_000,
        years=50,
        innovation_rate=0.05,
        seed=42,
    )

    print("\nConfiguration:")
    print(
        json.dumps(
            asdict(config),
            indent=2,
        )
    )

    print("\nRunning simulation...")

    profiler = Profiler()

    measured = profiler.measure(
        SimulationEngine().run,
        config,
    )

    result = measured["result"]

    print("\nSimulation complete.")

    print(
        f"Runtime: "
        f"{measured['runtime_seconds']:.6f} seconds"
    )

    print(
        f"Final productivity: "
        f"{result['final_productivity']:.6f}"
    )

    print(
        f"Productivity change: "
        f"{result['productivity_change']:.6f}"
    )

    print("\nReproducibility test:")

    reproducible = reproducibility_check()

    print(
        "PASS"
        if reproducible
        else "FAIL"
    )

    print("\nProject health:")

    health = check_project_health()

    print(
        f"Status: {health.status}"
    )

    for name, passed in health.checks.items():

        symbol = "PASS" if passed else "FAIL"

        print(
            f"  {symbol}: {name}"
        )

    print("\nRunning benchmark...")

    benchmark = run_benchmark(
        population=100_000,
        years=100,
        innovation_rate=0.05,
        seed=42,
    )

    print(
        f"Benchmark runtime: "
        f"{benchmark['runtime_seconds']:.6f} seconds"
    )

    print(
        f"Benchmark productivity: "
        f"{benchmark['final_productivity']:.6f}"
    )

    output = {
        "simulation": result,
        "benchmark": benchmark,
        "reproducible": reproducible,
        "health": {
            "status": health.status,
            "checks": health.checks,
            "details": health.details,
        },
    }

    output_path = save_json(
        output,
        "benchmark_results/gedt_rebuild_results.json",
    )

    print(
        f"\nResults written to: {output_path}"
    )

    print("\nGEDT rebuild finished.")


if __name__ == "__main__":
    main()