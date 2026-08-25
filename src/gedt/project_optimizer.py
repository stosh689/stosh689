"""GEDT project optimization and health analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .project_graph import (
    ProjectGraph,
    build_project_graph,
    summarize_project_graph,
)


@dataclass(frozen=True)
class OptimizationFinding:
    """One optimization finding."""

    category: str
    severity: str
    title: str
    description: str
    target: str | None = None
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "recommendation": self.recommendation,
        }


@dataclass
class ProjectOptimization:
    """Complete optimization result."""

    findings: list[OptimizationFinding]
    score: float
    healthy: bool
    source_count: int
    dependency_count: int
    node_count: int
    edge_count: int

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(
            finding.severity == "critical"
            for finding in self.findings
        )

    @property
    def high_count(self) -> int:
        return sum(
            finding.severity == "high"
            for finding in self.findings
        )

    @property
    def medium_count(self) -> int:
        return sum(
            finding.severity == "medium"
            for finding in self.findings
        )

    @property
    def low_count(self) -> int:
        return sum(
            finding.severity == "low"
            for finding in self.findings
        )

    @property
    def node_count_value(self) -> int:
        return self.node_count

    @property
    def edge_count_value(self) -> int:
        return self.edge_count

    @property
    def objective(self) -> float:
        return self.score

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "healthy": self.healthy,
            "source_count": self.source_count,
            "dependency_count": self.dependency_count,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "finding_count": self.finding_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
        }


def _findings_for_graph(
    graph: ProjectGraph,
) -> list[OptimizationFinding]:
    findings: list[OptimizationFinding] = []

    if graph.errors:
        for error in graph.errors:
            findings.append(
                OptimizationFinding(
                    category="correctness",
                    severity="high",
                    title="Python source parsing error",
                    description=error,
                    target=None,
                    recommendation=(
                        "Fix the syntax or encoding error so "
                        "the project graph can fully analyze "
                        "the repository."
                    ),
                )
            )

    if graph.has_cycle():
        findings.append(
            OptimizationFinding(
                category="architecture",
                severity="medium",
                title="Internal dependency cycle",
                description=(
                    "The project contains at least one cycle "
                    "between Python modules."
                ),
                target=None,
                recommendation=(
                    "Break the cycle by introducing a focused "
                    "interface or moving shared functionality "
                    "into a lower-level module."
                ),
            )
        )

    source_nodes = [
        node
        for node in graph.nodes.values()
        if node.kind == "file"
    ]

    outgoing: dict[str, set[str]] = {}

    for edge in graph.edges:
        if edge.kind == "dependency":
            outgoing.setdefault(
                edge.source,
                set(),
            ).add(edge.target)

    for node in source_nodes:
        count = len(
            outgoing.get(
                f"file:{node.name}",
                set(),
            )
        )

        if count >= 10:
            findings.append(
                OptimizationFinding(
                    category="architecture",
                    severity="medium",
                    title="High dependency fan-out",
                    description=(
                        f"Source file '{node.name}' "
                        f"references {count} dependencies."
                    ),
                    target=node.name,
                    recommendation=(
                        "Consider separating responsibilities "
                        "and reducing the module's dependency surface."
                    ),
                )
            )

    dependency_nodes = [
        node
        for node in graph.nodes.values()
        if node.kind == "dependency"
    ]

    incoming: dict[str, int] = {}

    for edge in graph.edges:
        if edge.kind == "dependency":
            incoming[edge.target] = (
                incoming.get(edge.target, 0) + 1
            )

    for node in dependency_nodes:
        count = incoming.get(
            node.name,
            0,
        )

        if count >= 8:
            findings.append(
                OptimizationFinding(
                    category="dependency",
                    severity="low",
                    title="Highly shared dependency",
                    description=(
                        f"Dependency '{node.name}' "
                        f"is referenced by {count} graph edges."
                    ),
                    target=node.name,
                    recommendation=(
                        "Keep this dependency stable and monitor "
                        "compatibility and security updates."
                    ),
                )
            )

    return findings


def optimize_project_graph(
    graph: ProjectGraph,
) -> ProjectOptimization:
    """Analyze an existing project graph."""

    findings = _findings_for_graph(graph)

    score = 100.0

    penalties = {
        "critical": 25.0,
        "high": 15.0,
        "medium": 8.0,
        "low": 3.0,
    }

    for finding in findings:
        score -= penalties.get(
            finding.severity,
            1.0,
        )

    score = max(
        0.0,
        min(100.0, score),
    )

    return ProjectOptimization(
        findings=findings,
        score=score,
        healthy=graph.healthy,
        source_count=len(graph.source_files()),
        dependency_count=len(graph.dependencies()),
        node_count=graph.node_count,
        edge_count=graph.edge_count,
    )


def optimize_project(
    root: str | Path,
) -> ProjectOptimization:
    """Build and optimize a project graph."""

    graph = build_project_graph(root)

    return optimize_project_graph(graph)


def analyze_project(
    root: str | Path,
) -> dict:
    """Return a JSON-compatible project analysis."""

    graph = build_project_graph(root)

    optimization = optimize_project_graph(
        graph
    )

    result = optimization.to_dict()

    result.update(
        summarize_project_graph(graph)
    )

    return result


def optimization_report(
    root: str | Path,
) -> str:
    """Create a human-readable optimization report."""

    graph = build_project_graph(root)
    result = optimize_project_graph(graph)

    status = (
        "PASS"
        if result.healthy
        else "FAIL"
    )

    return (
        "GEDT PROJECT OPTIMIZATION\n"
        "=========================\n"
        f"Status: {status}\n"
        f"Optimization score: "
        f"{result.score:.2f}/100\n"
        f"Source files: {result.source_count}\n"
        f"Dependencies: "
        f"{result.dependency_count}\n"
        f"Graph nodes: {result.node_count}\n"
        f"Graph edges: {result.edge_count}\n"
        f"Findings: {result.finding_count}\n"
        f"Critical: {result.critical_count}\n"
        f"High: {result.high_count}\n"
        f"Medium: {result.medium_count}\n"
        f"Low: {result.low_count}\n"
    )


__all__ = [
    "OptimizationFinding",
    "ProjectOptimization",
    "optimize_project",
    "optimize_project_graph",
    "analyze_project",
    "optimization_report",
]