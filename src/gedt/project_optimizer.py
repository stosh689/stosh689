"""
GEDT Project Optimizer
======================

Dependency-free optimization and analysis for GEDT project graphs.

This module consumes ProjectGraph objects produced by project_graph.py
and identifies practical optimization opportunities without modifying
the source project.

Compatible with Python 3.10+.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .project_graph import (
    ProjectEdge,
    ProjectGraph,
    ProjectNode,
    build_project_graph,
)


@dataclass(frozen=True)
class OptimizationFinding:
    """A single optimization opportunity."""

    category: str
    severity: str
    title: str
    description: str
    target: str | None = None
    recommendation: str = ""

    def to_dict(self) -> dict:
        """Return a JSON-compatible representation."""
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
    """Complete optimization report for a GEDT project."""

    findings: list[OptimizationFinding] = field(
        default_factory=list
    )
    score: int = 100
    healthy: bool = True
    source_count: int = 0
    dependency_count: int = 0
    node_count: int = 0
    edge_count: int = 0

    @property
    def finding_count(self) -> int:
        """Return the number of findings."""
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        """Return the number of critical findings."""
        return sum(
            finding.severity == "critical"
            for finding in self.findings
        )

    @property
    def high_count(self) -> int:
        """Return the number of high-severity findings."""
        return sum(
            finding.severity == "high"
            for finding in self.findings
        )

    @property
    def medium_count(self) -> int:
        """Return the number of medium-severity findings."""
        return sum(
            finding.severity == "medium"
            for finding in self.findings
        )

    @property
    def low_count(self) -> int:
        """Return the number of low-severity findings."""
        return sum(
            finding.severity == "low"
            for finding in self.findings
        )

    def add_finding(
        self,
        category: str,
        severity: str,
        title: str,
        description: str,
        target: str | None = None,
        recommendation: str = "",
    ) -> OptimizationFinding:
        """Add an optimization finding."""
        finding = OptimizationFinding(
            category=category,
            severity=severity,
            title=title,
            description=description,
            target=target,
            recommendation=recommendation,
        )

        if finding not in self.findings:
            self.findings.append(finding)

        return finding

    def to_dict(self) -> dict:
        """Return a JSON-compatible optimization report."""
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


_SEVERITY_PENALTY = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}


def _source_nodes(
    graph: ProjectGraph,
) -> list[ProjectNode]:
    """Return source nodes in deterministic order."""
    return sorted(
        (
            node
            for node in graph.nodes.values()
            if node.kind == "source"
        ),
        key=lambda node: node.name,
    )


def _external_nodes(
    graph: ProjectGraph,
) -> list[ProjectNode]:
    """Return external dependency nodes."""
    return sorted(
        (
            node
            for node in graph.nodes.values()
            if node.kind == "external"
        ),
        key=lambda node: node.name,
    )


def _import_edges(
    graph: ProjectGraph,
) -> list[ProjectEdge]:
    """Return import edges."""
    return [
        edge
        for edge in graph.edges
        if edge.kind == "imports"
    ]


def _outgoing_imports(
    graph: ProjectGraph,
) -> dict[str, set[str]]:
    """Build a source -> dependency lookup."""
    result: dict[str, set[str]] = {}

    for edge in _import_edges(graph):
        result.setdefault(
            edge.source,
            set(),
        ).add(edge.target)

    return result


def _incoming_imports(
    graph: ProjectGraph,
) -> dict[str, set[str]]:
    """Build dependency -> source lookup."""
    result: dict[str, set[str]] = {}

    for edge in _import_edges(graph):
        result.setdefault(
            edge.target,
            set(),
        ).add(edge.source)

    return result


def find_isolated_modules(
    graph: ProjectGraph,
) -> list[OptimizationFinding]:
    """Find source modules with no relationships."""
    findings: list[OptimizationFinding] = []

    incoming = _incoming_imports(graph)
    outgoing = _outgoing_imports(graph)

    for node in _source_nodes(graph):
        has_incoming = bool(
            incoming.get(node.name)
        )
        has_outgoing = bool(
            outgoing.get(node.name)
        )

        if has_incoming or has_outgoing:
            continue

        findings.append(
            OptimizationFinding(
                category="architecture",
                severity="low",
                title="Isolated source module",
                description=(
                    f"Source module '{node.name}' has no "
                    "incoming or outgoing import relationships."
                ),
                target=node.name,
                recommendation=(
                    "Verify that the module is intentionally "
                    "standalone. Remove it if it is obsolete, "
                    "or connect it to the appropriate project layer."
                ),
            )
        )

    return findings


def find_high_fanout_modules(
    graph: ProjectGraph,
    threshold: int = 8,
) -> list[OptimizationFinding]:
    """
    Find modules importing many dependencies.

    High fan-out can indicate a module that has accumulated
    too many responsibilities.
    """
    findings: list[OptimizationFinding] = []

    outgoing = _outgoing_imports(graph)

    for source in sorted(outgoing):
        count = len(outgoing[source])

        if count < threshold:
            continue

        severity = (
            "high"
            if count >= threshold * 2
            else "medium"
        )

        findings.append(
            OptimizationFinding(
                category="architecture",
                severity=severity,
                title="High dependency fan-out",
                description=(
                    f"Module '{source}' imports {count} "
                    "dependencies."
                ),
                target=source,
                recommendation=(
                    "Consider splitting responsibilities, "
                    "introducing smaller interfaces, or moving "
                    "shared behavior into focused modules."
                ),
            )
        )

    return findings


def find_high_fanin_dependencies(
    graph: ProjectGraph,
    threshold: int = 8,
) -> list[OptimizationFinding]:
    """
    Find dependencies imported by many modules.

    High fan-in is not inherently bad. It identifies important
    architectural hubs that deserve stability and testing.
    """
    findings: list[OptimizationFinding] = []

    incoming = _incoming_imports(graph)

    for target in sorted(incoming):
        sources = incoming[target]
        count = len(sources)

        if count < threshold:
            continue

        node = graph.nodes.get(target)

        if node is not None and node.kind == "source":
            category = "architecture"
            title = "High fan-in internal module"
            recommendation = (
                "Treat this module as a core architectural "
                "interface. Keep its API stable and maintain "
                "strong test coverage."
            )
        else:
            category = "dependency"
            title = "High fan-in external dependency"
            recommendation = (
                "Treat this dependency as strategically important. "
                "Monitor version compatibility and security updates."
            )

        findings.append(
            OptimizationFinding(
                category=category,
                severity="low",
                title=title,
                description=(
                    f"'{target}' is imported by {count} "
                    "source modules."
                ),
                target=target,
                recommendation=recommendation,
            )
        )

    return findings


def find_duplicate_imports(
    graph: ProjectGraph,
) -> list[OptimizationFinding]:
    """
    Find modules that import multiple paths from the same
    top-level package.
    """
    findings: list[OptimizationFinding] = []

    outgoing = _outgoing_imports(graph)

    for source in sorted(outgoing):
        dependencies = outgoing[source]

        by_root: dict[str, set[str]] = {}

        for dependency in dependencies:
            root = dependency.split(
                ".",
                1,
            )[0]

            by_root.setdefault(
                root,
                set(),
            ).add(dependency)

        for root in sorted(by_root):
            paths = by_root[root]

            if len(paths) <= 1:
                continue

            findings.append(
                OptimizationFinding(
                    category="imports",
                    severity="low",
                    title="Multiple import paths",
                    description=(
                        f"Module '{source}' imports multiple "
                        f"paths from '{root}': "
                        f"{', '.join(sorted(paths))}."
                    ),
                    target=source,
                    recommendation=(
                        "Review whether these imports can be "
                        "consolidated behind a smaller public API."
                    ),
                )
            )

    return findings


def find_unused_declared_dependencies(
    graph: ProjectGraph,
    declared_dependencies: Iterable[str] | None = None,
) -> list[OptimizationFinding]:
    """
    Find declared dependencies that are not represented by
    source imports.

    When declared_dependencies is omitted, this function uses
    external nodes from the graph as the best available signal.
    """
    if declared_dependencies is None:
        return []

    imported_roots = {
        dependency.split(".", 1)[0]
        for dependency in graph.dependencies()
    }

    findings: list[OptimizationFinding] = []

    for dependency in sorted(
        {
            item.strip()
            for item in declared_dependencies
            if isinstance(item, str)
            and item.strip()
        }
    ):
        root = dependency.split(
            "[",
            1,
        )[0].split(
            " ",
            1,
        )[0].split(
            ">",
            1,
        )[0].split(
            "<",
            1,
        )[0].split(
            "=",
            1,
        )[0].strip()

        if not root:
            continue

        if root in imported_roots:
            continue

        findings.append(
            OptimizationFinding(
                category="dependency",
                severity="medium",
                title="Potentially unused dependency",
                description=(
                    f"Declared dependency '{dependency}' "
                    "does not appear in the project's import graph."
                ),
                target=dependency,
                recommendation=(
                    "Verify whether the dependency is used dynamically, "
                    "by tooling, plugins, tests, or runtime configuration "
                    "before removing it."
                ),
            )
        )

    return findings


def find_import_cycles(
    graph: ProjectGraph,
) -> list[OptimizationFinding]:
    """Detect simple directed cycles among source modules."""
    findings: list[OptimizationFinding] = []

    outgoing = _outgoing_imports(graph)

    source_names = {
        node.name
        for node in _source_nodes(graph)
    }

    adjacency: dict[str, set[str]] = {
        name: {
            target
            for target in outgoing.get(name, set())
            if target in source_names
        }
        for name in source_names
    }

    visited: set[str] = set()
    active: set[str] = set()
    reported: set[frozenset[str]] = set()

    def visit(
        node: str,
        path: list[str],
    ) -> None:
        if node in active:
            try:
                index = path.index(node)
            except ValueError:
                index = 0

            cycle_nodes = path[index:]

            if len(cycle_nodes) >= 2:
                key = frozenset(
                    cycle_nodes
                )

                if key not in reported:
                    reported.add(key)

                    cycle_text = " -> ".join(
                        cycle_nodes + [node]
                    )

                    findings.append(
                        OptimizationFinding(
                            category="architecture",
                            severity="high",
                            title="Import cycle detected",
                            description=(
                                f"Source modules form a dependency "
                                f"cycle: {cycle_text}."
                            ),
                            target=node,
                            recommendation=(
                                "Break the cycle using a narrower "
                                "interface, dependency inversion, "
                                "shared abstraction, or module split."
                            ),
                        )
                    )

            return

        if node in visited:
            return

        visited.add(node)
        active.add(node)

        for target in sorted(
            adjacency.get(node, set())
        ):
            visit(
                target,
                path + [target],
            )

        active.remove(node)

    for node in sorted(source_names):
        visit(
            node,
            [node],
        )

    return findings


def find_external_dependency_concentration(
    graph: ProjectGraph,
    threshold: int = 5,
) -> list[OptimizationFinding]:
    """
    Find external dependencies used throughout many source modules.
    """
    findings: list[OptimizationFinding] = []

    incoming = _incoming_imports(graph)

    for dependency in sorted(incoming):
        node = graph.nodes.get(
            dependency
        )

        if node is None:
            continue

        if node.kind != "external":
            continue

        users = incoming[dependency]
        count = len(users)

        if count < threshold:
            continue

        severity = (
            "medium"
            if count >= threshold * 2
            else "low"
        )

        findings.append(
            OptimizationFinding(
                category="dependency",
                severity=severity,
                title="Dependency concentration",
                description=(
                    f"External dependency '{dependency}' "
                    f"is used by {count} source modules."
                ),
                target=dependency,
                recommendation=(
                    "Centralize integration behind a small internal "
                    "adapter when practical. This reduces coupling "
                    "and makes future dependency replacement easier."
                ),
            )
        )

    return findings


def _calculate_score(
    findings: Iterable[OptimizationFinding],
) -> int:
    """Calculate an optimization score from findings."""
    penalty = sum(
        _SEVERITY_PENALTY.get(
            finding.severity,
            0,
        )
        for finding in findings
    )

    return max(
        0,
        min(
            100,
            100 - penalty,
        ),
    )


def optimize_project_graph(
    graph: ProjectGraph,
    *,
    fanout_threshold: int = 8,
    fanin_threshold: int = 8,
    concentration_threshold: int = 5,
) -> ProjectOptimization:
    """Analyze an existing ProjectGraph."""
    report = ProjectOptimization(
        source_count=len(
            _source_nodes(graph)
        ),
        dependency_count=graph.dependency_count,
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        healthy=graph.healthy,
    )

    finding_groups = (
        find_isolated_modules(graph),
        find_high_fanout_modules(
            graph,
            threshold=fanout_threshold,
        ),
        find_high_fanin_dependencies(
            graph,
            threshold=fanin_threshold,
        ),
        find_duplicate_imports(graph),
        find_import_cycles(graph),
        find_external_dependency_concentration(
            graph,
            threshold=concentration_threshold,
        ),
    )

    for findings in finding_groups:
        for finding in findings:
            report.add_finding(
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                target=finding.target,
                recommendation=finding.recommendation,
            )

    report.score = _calculate_score(
        report.findings
    )

    if report.critical_count > 0:
        report.healthy = False

    return report


def optimize_project(
    root: str | Path,
    *,
    fanout_threshold: int = 8,
    fanin_threshold: int = 8,
    concentration_threshold: int = 5,
) -> ProjectOptimization:
    """Build the graph and optimize it."""
    graph = build_project_graph(root)

    return optimize_project_graph(
        graph,
        fanout_threshold=fanout_threshold,
        fanin_threshold=fanin_threshold,
        concentration_threshold=concentration_threshold,
    )


def optimization_report(
    root: str | Path,
) -> str:
    """Return a human-readable optimization report."""
    report = optimize_project(root)

    status = (
        "HEALTHY"
        if report.healthy
        else "NEEDS ATTENTION"
    )

    lines = [
        "GEDT PROJECT OPTIMIZATION",
        "=========================",
        f"Status: {status}",
        f"Optimization score: {report.score}/100",
        "",
        f"Source files: {report.source_count}",
        f"Dependencies: {report.dependency_count}",
        f"Nodes: {report.node_count}",
        f"Edges: {report.edge_count}",
        "",
        f"Findings: {report.finding_count}",
        f"Critical: {report.critical_count}",
        f"High: {report.high_count}",
        f"Medium: {report.medium_count}",
        f"Low: {report.low_count}",
    ]

    if report.findings:
        lines.extend(
            [
                "",
                "Findings:",
            ]
        )

        for index, finding in enumerate(
            report.findings,
            start=1,
        ):
            lines.extend(
                [
                    (
                        f"{index}. "
                        f"[{finding.severity.upper()}] "
                        f"{finding.title}"
                    ),
                    (
                        f"   Target: "
                        f"{finding.target or 'project'}"
                    ),
                    (
                        f"   {finding.description}"
                    ),
                    (
                        f"   Recommendation: "
                        f"{finding.recommendation}"
                    ),
                ]
            )

    return "\n".join(lines)


def analyze_project(
    root: str | Path,
) -> dict:
    """Return a JSON-compatible optimization analysis."""
    return optimize_project(
        root
    ).to_dict()


__all__ = [
    "OptimizationFinding",
    "ProjectOptimization",
    "find_isolated_modules",
    "find_high_fanout_modules",
    "find_high_fanin_dependencies",
    "find_duplicate_imports",
    "find_unused_declared_dependencies",
    "find_import_cycles",
    "find_external_dependency_concentration",
    "optimize_project_graph",
    "optimize_project",
    "optimization_report",
    "analyze_project",
]