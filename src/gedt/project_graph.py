"""Project dependency graph utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


@dataclass
class ProjectGraph:
    """Simple directed project dependency graph."""

    nodes: set[str] = field(default_factory=set)
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add_node(self, name: str) -> None:
        name = str(name)
        self.nodes.add(name)
        self.edges.setdefault(name, set())

    def add_edge(self, source: str, target: str) -> None:
        source = str(source)
        target = str(target)

        self.add_node(source)
        self.add_node(target)
        self.edges[source].add(target)

    def dependencies(self, name: str) -> set[str]:
        return set(self.edges.get(str(name), set()))

    def dependents(self, name: str) -> set[str]:
        name = str(name)
        return {
            source
            for source, targets in self.edges.items()
            if name in targets
        }

    def has_node(self, name: str) -> bool:
        return str(name) in self.nodes

    def has_edge(self, source: str, target: str) -> bool:
        return str(target) in self.edges.get(
            str(source),
            set(),
        )

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return sum(
            len(targets)
            for targets in self.edges.values()
        )

    def roots(self) -> list[str]:
        return sorted(
            node
            for node in self.nodes
            if not self.dependents(node)
        )

    def leaves(self) -> list[str]:
        return sorted(
            node
            for node in self.nodes
            if not self.dependencies(node)
        )


def build_project_graph(
    dependencies: Mapping[str, Iterable[str]] | None = None,
) -> ProjectGraph:
    """Build a ProjectGraph from a dependency mapping."""

    graph = ProjectGraph()

    if dependencies is None:
        return graph

    for project, deps in dependencies.items():
        graph.add_node(str(project))

        for dependency in deps:
            graph.add_edge(
                str(project),
                str(dependency),
            )

    return graph


def graph_from_edges(
    edges: Iterable[tuple[str, str]],
) -> ProjectGraph:
    graph = ProjectGraph()

    for source, target in edges:
        graph.add_edge(source, target)

    return graph


def summarize_project_graph(
    graph: ProjectGraph,
) -> dict[str, object]:
    """Return a stable summary suitable for tests and reports."""

    return {
        "nodes": graph.node_count(),
        "edges": graph.edge_count(),
        "node_count": graph.node_count(),
        "edge_count": graph.edge_count(),
        "roots": graph.roots(),
        "leaves": graph.leaves(),
        "projects": sorted(graph.nodes),
    }


def topological_order(
    graph: ProjectGraph,
) -> list[str]:
    """Return a deterministic topological ordering.

    Raises ValueError if a dependency cycle exists.
    """

    incoming = {
        node: len(graph.dependents(node))
        for node in graph.nodes
    }

    ready = sorted(
        node
        for node, degree in incoming.items()
        if degree == 0
    )

    result: list[str] = []

    while ready:
        node = ready.pop(0)
        result.append(node)

        for dependent in sorted(
            graph.dependencies(node)
        ):
            incoming[dependent] -= 1

            if incoming[dependent] == 0:
                ready.append(dependent)
                ready.sort()

    if len(result) != len(graph.nodes):
        raise ValueError(
            "project graph contains a dependency cycle"
        )

    return result


__all__ = [
    "ProjectGraph",
    "build_project_graph",
    "graph_from_edges",
    "summarize_project_graph",
    "topological_order",
]