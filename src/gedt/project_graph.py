"""GEDT project dependency graph analysis."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass(frozen=True)
class ProjectNode:
    """A node in the project graph."""

    name: str
    kind: str
    path: str | None = None


@dataclass(frozen=True)
class ProjectEdge:
    """A directed graph relationship."""

    source: str
    target: str
    kind: str = "dependency"


@dataclass
class ProjectGraph:
    """Dependency graph for a GEDT project."""

    nodes: dict[str, ProjectNode] = field(default_factory=dict)
    edges: list[ProjectEdge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    root: str | None = None

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
        """Return external dependency names."""
        return sorted(
            {
                edge.target
                for edge in self.edges
                if edge.kind == "dependency"
            }
        )

    def dependency_names(self) -> list[str]:
        return self.dependencies()

    def source_files(self) -> list[str]:
        return sorted(
            node.name
            for node in self.nodes.values()
            if node.kind == "file"
        )

    def has_cycle(self) -> bool:
        """Detect cycles between internal modules."""

        adjacency: dict[str, set[str]] = {}

        for edge in self.edges:
            if edge.kind == "module":
                adjacency.setdefault(
                    edge.source,
                    set(),
                ).add(edge.target)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True

            if node in visited:
                return False

            visiting.add(node)

            for child in adjacency.get(node, set()):
                if visit(child):
                    return True

            visiting.remove(node)
            visited.add(node)

            return False

        return any(
            visit(node)
            for node in adjacency
        )


def _module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).with_suffix("")

    parts = list(relative.parts)

    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts) or root.name


def _dependency_name(name: str) -> str:
    return name.split(".", 1)[0]


def _project_name(root: Path) -> str:
    pyproject = root / "pyproject.toml"

    if pyproject.exists():
        text = pyproject.read_text(
            encoding="utf-8",
            errors="replace",
        )

        match = re.search(
            r"^name\s*=\s*[\"']([^\"']+)[\"']",
            text,
            re.MULTILINE,
        )

        if match:
            return match.group(1)

    return root.name


def _pyproject_dependencies(root: Path) -> set[str]:
    """Extract simple PEP 621 dependencies."""

    path = root / "pyproject.toml"

    if not path.exists():
        return set()

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    dependencies: set[str] = set()

    in_dependencies = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("dependencies"):
            in_dependencies = True

        if in_dependencies:
            match = re.search(
                r"[\"']([A-Za-z0-9_.-]+)",
                stripped,
            )

            if match:
                name = match.group(1)

                if name not in {
                    "dependencies",
                    "project",
                }:
                    dependencies.add(name)

        if in_dependencies and stripped == "]":
            break

    return dependencies


def build_project_graph(
    root: str | Path,
) -> ProjectGraph:
    """Build a dependency graph from a project directory."""

    root = Path(root).resolve()

    graph = ProjectGraph(
        root=root.name,
    )

    project_name = _project_name(root)

    project_key = f"project:{project_name}"

    graph.nodes[project_key] = ProjectNode(
        name=project_name,
        kind="project",
        path=str(root),
    )

    module_nodes: dict[str, str] = {}

    python_files = sorted(
        root.rglob("*.py")
    )

    for path in python_files:
        if any(
            part in {
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                "node_modules",
            }
            for part in path.parts
        ):
            continue

        module = _module_name(
            root,
            path,
        )

        node_key = f"file:{module}"

        module_nodes[module] = node_key

        graph.nodes[node_key] = ProjectNode(
            name=module,
            kind="file",
            path=str(path),
        )

        graph.edges.append(
            ProjectEdge(
                source=project_key,
                target=node_key,
                kind="contains",
            )
        )

        try:
            source = path.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(
                source,
                filename=str(path),
            )

        except (
            SyntaxError,
            UnicodeDecodeError,
            OSError,
        ) as exc:
            graph.errors.append(
                f"{path}: {exc}"
            )
            continue

        for node in ast.walk(tree):

            names: list[str] = []

            if isinstance(
                node,
                ast.Import,
            ):
                names = [
                    alias.name
                    for alias in node.names
                ]

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                if node.module:
                    names = [node.module]

            for name in names:

                dependency = _dependency_name(
                    name
                )

                dependency_key = (
                    f"dependency:{dependency}"
                )

                if dependency_key not in graph.nodes:
                    graph.nodes[
                        dependency_key
                    ] = ProjectNode(
                        name=dependency,
                        kind="dependency",
                    )

                graph.edges.append(
                    ProjectEdge(
                        source=node_key,
                        target=dependency,
                        kind="dependency",
                    )
                )

                if name in module_nodes:
                    graph.edges.append(
                        ProjectEdge(
                            source=node_key,
                            target=module_nodes[name],
                            kind="module",
                        )
                    )

    for dependency in sorted(
        _pyproject_dependencies(root)
    ):
        dependency_key = (
            f"dependency:{dependency}"
        )

        if dependency_key not in graph.nodes:
            graph.nodes[
                dependency_key
            ] = ProjectNode(
                name=dependency,
                kind="dependency",
            )

        graph.edges.append(
            ProjectEdge(
                source=project_key,
                target=dependency,
                kind="dependency",
            )
        )

    return graph


def summarize_project_graph(
    graph: ProjectGraph,
) -> dict:
    """Return deterministic JSON-compatible graph summary."""

    files = graph.source_files()
    dependencies = graph.dependencies()

    return {
        "file_count": len(files),
        "dependency_count": len(dependencies),
        "files": files,
        "dependencies": dependencies,
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "healthy": graph.healthy,
        "errors": list(graph.errors),
        "has_cycle": graph.has_cycle(),
    }


__all__ = [
    "ProjectNode",
    "ProjectEdge",
    "ProjectGraph",
    "build_project_graph",
    "summarize_project_graph",
]