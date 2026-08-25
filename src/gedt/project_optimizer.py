"""Project optimization utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .project_graph import (
    ProjectGraph,
    build_project_graph,
    topological_order,
)


@dataclass(frozen=True)
class ProjectOptimization:
    """Result of project optimization."""

    selected_projects: tuple[str, ...]
    total_cost: float
    total_value: float
    score: float
    feasible: bool

    @property
    def projects(self) -> tuple[str, ...]:
        return self.selected_projects

    @property
    def objective(self) -> float:
        return self.score


def _normalise_values(
    values: Mapping[str, float] | None,
) -> dict[str, float]:
    if values is None:
        return {}

    return {
        str(key): float(value)
        for key, value in values.items()
    }


def optimize_project(
    projects: Sequence[str] | None = None,
    *,
    costs: Mapping[str, float] | None = None,
    values: Mapping[str, float] | None = None,
    budget: float | None = None,
) -> ProjectOptimization:
    """Choose projects using a deterministic value/cost heuristic."""

    project_list = [
        str(project)
        for project in (
            projects
            if projects is not None
            else []
        )
    ]

    cost_map = _normalise_values(costs)
    value_map = _normalise_values(values)

    if budget is None:
        budget = float("inf")
    else:
        budget = float(budget)

    if budget < 0:
        raise ValueError(
            "budget cannot be negative"
        )

    ranked = []

    for project in project_list:
        cost = cost_map.get(project, 0.0)
        value = value_map.get(project, 0.0)

        if cost < 0:
            raise ValueError(
                f"cost for {project!r} cannot be negative"
            )

        ratio = (
            value / cost
            if cost > 0
            else (
                float("inf")
                if value > 0
                else 0.0
            )
        )

        ranked.append(
            (
                -ratio,
                -value,
                cost,
                project,
            )
        )

    ranked.sort()

    selected: list[str] = []
    total_cost = 0.0
    total_value = 0.0

    for _, _, cost, project in ranked:
        if total_cost + cost > budget:
            continue

        selected.append(project)
        total_cost += cost
        total_value += value_map.get(
            project,
            0.0,
        )

    score = (
        total_value / total_cost
        if total_cost > 0
        else total_value
    )

    return ProjectOptimization(
        selected_projects=tuple(selected),
        total_cost=total_cost,
        total_value=total_value,
        score=score,
        feasible=total_cost <= budget,
    )


def optimize_project_graph(
    graph: ProjectGraph,
    *,
    costs: Mapping[str, float] | None = None,
    values: Mapping[str, float] | None = None,
    budget: float | None = None,
) -> ProjectOptimization:
    """Optimize projects while respecting graph ordering."""

    order = topological_order(graph)

    result = optimize_project(
        order,
        costs=costs,
        values=values,
        budget=budget,
    )

    return result


def optimization_report(
    result: ProjectOptimization,
) -> str:
    status = (
        "PASS"
        if result.feasible
        else "FAIL"
    )

    projects = ", ".join(
        result.selected_projects
    )

    return (
        "PROJECT OPTIMIZATION REPORT\n"
        "===========================\n"
        f"Status: {status}\n"
        f"Projects: {projects}\n"
        f"Total Cost: {result.total_cost:.6f}\n"
        f"Total Value: {result.total_value:.6f}\n"
        f"Score: {result.score:.6f}\n"
        f"Feasible: {result.feasible}\n"
    )


def analyze_project(
    dependencies: Mapping[str, Iterable[str]] | None = None,
    *,
    costs: Mapping[str, float] | None = None,
    values: Mapping[str, float] | None = None,
    budget: float | None = None,
) -> ProjectOptimization:
    """Build a project graph and optimize it."""

    graph = build_project_graph(
        dependencies
    )

    return optimize_project_graph(
        graph,
        costs=costs,
        values=values,
        budget=budget,
    )


__all__ = [
    "ProjectOptimization",
    "optimize_project",
    "optimize_project_graph",
    "optimization_report",
    "analyze_project",
]