from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectNode:
    """A node in the GEDT project graph."""

    id: str
    kind: str
    name: str
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectEdge:
    """A directed relationship between two project nodes."""

    source: str
    target: str
    kind: str


@dataclass
class ProjectGraph:
    """Normalized representation of a software project."""

    root: Path
    nodes: dict[str, ProjectNode] = field(default_factory=dict)
    edges: list[ProjectEdge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_node(self, node: ProjectNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ProjectEdge) -> None:
        if edge not in self.edges:
            self.edges.append(edge)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def healthy(self) -> bool:
        return not self.errors

    def dependencies(self) -> list[str]:
        """Return normalized dependency names found in the graph."""
        return sorted(
            node.name
            for node in self.nodes.values()
            if node.kind == "dependency"
        )

    def files(self) -> list[str]:
        """Return project files represented in the graph."""
        return sorted(
            node.path
            for node in self.nodes.values()
            if node.kind == "file" and node.path is not None
        )


def _node_id(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _add_file_node(graph: ProjectGraph, path: Path) -> str:
    relative = path.relative_to(graph.root).as_posix()
    node_id = _node_id("file", relative)

    graph.add_node(
        ProjectNode(
            id=node_id,
            kind="file",
            name=path.name,
            path=relative,
        )
    )

    return node_id


def _add_dependency(
    graph: ProjectGraph,
    dependency: str,
) -> str:
    dependency = dependency.strip()

    node_id = _node_id("dependency", dependency)

    graph.add_node(
        ProjectNode(
            id=node_id,
            kind="dependency",
            name=dependency,
        )
    )

    return node_id


def _parse_python(
    graph: ProjectGraph,
    path: Path,
    file_node_id: str,
) -> None:
    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        graph.errors.append(
            f"{path.relative_to(graph.root)}: {exc}"
        )
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependency = alias.name.split(".")[0]
                dependency_id = _add_dependency(
                    graph,
                    dependency,
                )

                graph.add_edge(
                    ProjectEdge(
                        source=file_node_id,
                        target=dependency_id,
                        kind="imports",
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                dependency = node.module.split(".")[0]
                dependency_id = _add_dependency(
                    graph,
                    dependency,
                )

                graph.add_edge(
                    ProjectEdge(
                        source=file_node_id,
                        target=dependency_id,
                        kind="imports",
                    )
                )


def _parse_json(
    graph: ProjectGraph,
    path: Path,
    file_node_id: str,
) -> None:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        graph.errors.append(
            f"{path.relative_to(graph.root)}: {exc}"
        )
        return

    if isinstance(data, dict):
        metadata_id = _node_id(
            "json-object",
            path.relative_to(graph.root).as_posix(),
        )

        graph.add_node(
            ProjectNode(
                id=metadata_id,
                kind="configuration",
                name=path.name,
                path=path.relative_to(graph.root).as_posix(),
                metadata={
                    "keys": sorted(str(key) for key in data),
                },
            )
        )

        graph.add_edge(
            ProjectEdge(
                source=file_node_id,
                target=metadata_id,
                kind="contains",
            )
        )


def _parse_toml(
    graph: ProjectGraph,
    path: Path,
    file_node_id: str,
) -> None:
    try:
        import tomllib

        with path.open("rb") as file:
            data = tomllib.load(file)

    except (OSError, ValueError) as exc:
        graph.errors.append(
            f"{path.relative_to(graph.root)}: {exc}"
        )
        return

    if not isinstance(data, dict):
        return

    project = data.get("project")

    if isinstance(project, dict):
        name = project.get("name")

        if isinstance(name, str):
            project_node_id = _node_id(
                "project",
                name,
            )

            graph.add_node(
                ProjectNode(
                    id=project_node_id,
                    kind="project",
                    name=name,
                    path=path.relative_to(graph.root).as_posix(),
                    metadata={
                        "version": project.get("version"),
                        "requires_python": project.get(
                            "requires-python"
                        ),
                    },
                )
            )

            graph.add_edge(
                ProjectEdge(
                    source=file_node_id,
                    target=project_node_id,
                    kind="defines",
                )
            )

        dependencies = project.get(
            "dependencies",
            [],
        )

        if isinstance(dependencies, list):
            for dependency in dependencies:
                if not isinstance(dependency, str):
                    continue

                dependency_name = (
                    dependency.split(";", 1)[0]
                    .split("[", 1)[0]
                    .strip()
                )

                if not dependency_name:
                    continue

                dependency_id = _add_dependency(
                    graph,
                    dependency_name,
                )

                graph.add_edge(
                    ProjectEdge(
                        source=file_node_id,
                        target=dependency_id,
                        kind="declares",
                    )
                )


def build_project_graph(
    root: str | Path,
) -> ProjectGraph:
    """
    Build a normalized project graph.

    Unknown file types are represented as ordinary file nodes.
    Parse failures are recorded in ``graph.errors`` rather than
    aborting the entire project scan.
    """
    root_path = Path(root).resolve()

    if not root_path.exists():
        raise FileNotFoundError(
            f"Project root does not exist: {root_path}"
        )

    if not root_path.is_dir():
        raise NotADirectoryError(
            f"Project root is not a directory: {root_path}"
        )

    graph = ProjectGraph(root=root_path)

    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue

        # Avoid scanning common generated/environment directories.
        if any(
            part in {
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                "node_modules",
                "dist",
                "build",
            }
            for part in path.parts
        ):
            continue

        file_node_id = _add_file_node(
            graph,
            path,
        )

        suffix = path.suffix.lower()
        name = path.name.lower()

        if suffix == ".py":
            _parse_python(
                graph,
                path,
                file_node_id,
            )

        elif suffix == ".json":
            _parse_json(
                graph,
                path,
                file_node_id,
            )

        elif suffix == ".toml" or name == "pyproject.toml":
            _parse_toml(
                graph,
                path,
                file_node_id,
            )

    return graph


def summarize_project_graph(
    graph: ProjectGraph,
) -> dict[str, Any]:
    """Return a deterministic summary suitable for APIs and benchmarks."""
    return {
        "root": str(graph.root),
        "healthy": graph.healthy,
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "file_count": len(graph.files()),
        "dependency_count": len(graph.dependencies()),
        "dependencies": graph.dependencies(),
        "errors": list(graph.errors),
    }


__all__ = [
    "ProjectEdge",
    "ProjectGraph",
    "ProjectNode",
    "build_project_graph",
    "summarize_project_graph",
]