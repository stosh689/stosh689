"""
GEDT Project Graph
==================

Builds a lightweight dependency graph from Python source files and
pyproject.toml metadata.

Designed to be:
- Python 3.10+
- dependency-free
- deterministic
- easy to test
- compatible with the existing GEDT project-health tooling
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ProjectNode:
    """A node in the project graph."""

    name: str
    path: str | None = None
    kind: str = "module"


@dataclass(frozen=True)
class ProjectEdge:
    """A directed relationship between two project nodes."""

    source: str
    target: str
    kind: str = "imports"


@dataclass
class ProjectGraph:
    """Dependency graph for a Python project."""

    nodes: dict[str, ProjectNode] = field(default_factory=dict)
    edges: list[ProjectEdge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    healthy: bool = True

    def add_node(
        self,
        name: str,
        path: str | Path | None = None,
        kind: str = "module",
    ) -> ProjectNode:
        """Add a node to the graph if it does not already exist."""
        normalized_path = str(path) if path is not None else None

        if name not in self.nodes:
            self.nodes[name] = ProjectNode(
                name=name,
                path=normalized_path,
                kind=kind,
            )

        return self.nodes[name]

    def add_edge(
        self,
        source: str,
        target: str,
        kind: str = "imports",
    ) -> ProjectEdge:
        """Add an edge to the graph without creating duplicates."""
        self.add_node(source)
        self.add_node(target)

        edge = ProjectEdge(
            source=source,
            target=target,
            kind=kind,
        )

        if edge not in self.edges:
            self.edges.append(edge)

        return edge

    @property
    def node_count(self) -> int:
        """Number of nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Number of edges."""
        return len(self.edges)

    @property
    def dependency_count(self) -> int:
        """Number of unique imported dependencies."""
        return len(self.dependencies())

    def dependencies(self) -> list[str]:
        """Return unique dependency names in deterministic order."""
        return sorted(
            {
                edge.target
                for edge in self.edges
                if edge.kind == "imports"
            }
        )

    def dependencies_of(self, name: str) -> list[str]:
        """Return direct dependencies of a node."""
        return sorted(
            {
                edge.target
                for edge in self.edges
                if edge.source == name
            }
        )

    def dependents_of(self, name: str) -> list[str]:
        """Return nodes that depend on the supplied node."""
        return sorted(
            {
                edge.source
                for edge in self.edges
                if edge.target == name
            }
        )

    def has_node(self, name: str) -> bool:
        """Return True when a node exists."""
        return name in self.nodes

    def has_edge(
        self,
        source: str,
        target: str,
        kind: str = "imports",
    ) -> bool:
        """Return True when an edge exists."""
        return ProjectEdge(
            source=source,
            target=target,
            kind=kind,
        ) in self.edges

    def isolated_nodes(self) -> list[str]:
        """Return nodes with no incoming or outgoing edges."""
        connected: set[str] = set()

        for edge in self.edges:
            connected.add(edge.source)
            connected.add(edge.target)

        return sorted(
            name
            for name in self.nodes
            if name not in connected
        )

    def to_dict(self) -> dict:
        """Return a JSON-compatible representation."""
        return {
            "nodes": [
                {
                    "name": node.name,
                    "path": node.path,
                    "kind": node.kind,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "kind": edge.kind,
                }
                for edge in self.edges
            ],
            "errors": list(self.errors),
            "healthy": self.healthy,
        }


def extract_imports(source: str) -> list[str]:
    """
    Extract imported module names from Python source.

    Both normal imports and from-import statements are supported.
    """
    tree = ast.parse(source)

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return sorted(imports)


def extract_imports_from_file(path: str | Path) -> list[str]:
    """Read a Python file and extract its imports."""
    file_path = Path(path)

    source = file_path.read_text(
        encoding="utf-8",
    )

    return extract_imports(source)


def _python_files(root: Path) -> Iterable[Path]:
    """Yield Python source files while skipping generated directories."""
    excluded = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "dist",
        "build",
        "*.egg-info",
    }

    for path in root.rglob("*.py"):
        if any(
            part in excluded
            for part in path.parts
        ):
            continue

        if path.is_file():
            yield path


def _module_name(root: Path, path: Path) -> str:
    """
    Convert a Python path into a module-style name.

    Example:

        src/gedt/project_graph.py

    becomes:

        src.gedt.project_graph
    """
    relative = path.relative_to(root)

    parts = list(relative.parts)

    if not parts:
        return ""

    filename = parts[-1]

    if filename == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(filename).stem

    return ".".join(parts)


def _top_level_module(import_name: str) -> str:
    """Return the top-level component of an import."""
    return import_name.split(".", 1)[0]


def _dependency_name(value: str) -> str:
    """
    Normalize a PEP 508 dependency into a readable package name.

    Examples:

        numpy>=1.0       -> numpy
        requests==2.0    -> requests
        fastapi[standard] -> fastapi
    """
    value = value.strip()

    if not value:
        return ""

    value = value.split("[", 1)[0]

    separators = (
        ">=",
        "<=",
        "==",
        "~=",
        "!=",
        ">",
        "<",
        ";",
    )

    for separator in separators:
        value = value.split(separator, 1)[0]

    return value.strip()


def _read_pyproject(
    root: Path,
    graph: ProjectGraph,
) -> None:
    """
    Read project metadata and dependencies from pyproject.toml.
    """
    pyproject = root / "pyproject.toml"

    if not pyproject.is_file():
        return

    try:
        import tomllib

        with pyproject.open("rb") as file:
            data = tomllib.load(file)

    except (OSError, ValueError) as exc:
        graph.errors.append(
            f"pyproject.toml: {exc}"
        )
        graph.healthy = False
        return

    project = data.get("project", {})

    if not isinstance(project, dict):
        graph.errors.append(
            "pyproject.toml: [project] must be a table"
        )
        graph.healthy = False
        return

    project_name = project.get("name")

    if isinstance(project_name, str):
        project_name = project_name.strip()

        if project_name:
            graph.add_node(
                project_name,
                path=pyproject,
                kind="project",
            )

    dependencies = project.get(
        "dependencies",
        [],
    )

    if not isinstance(dependencies, list):
        return

    for dependency in dependencies:
        if not isinstance(dependency, str):
            continue

        package_name = _dependency_name(
            dependency
        )

        if package_name:
            graph.add_node(
                package_name,
                kind="external",
            )


def build_project_graph(
    root: str | Path,
) -> ProjectGraph:
    """
    Build a dependency graph for a project.

    Python source files become source nodes.
    External imports become external nodes.
    pyproject.toml metadata becomes project/dependency nodes.
    """
    root_path = Path(root).resolve()

    graph = ProjectGraph()

    files = list(
        _python_files(root_path)
    )

    module_by_name: dict[str, Path] = {}

    for path in files:
        module = _module_name(
            root_path,
            path,
        )

        if not module:
            continue

        module_by_name[module] = path

        graph.add_node(
            module,
            path=path,
            kind="source",
        )

    for path in files:
        source_module = _module_name(
            root_path,
            path,
        )

        if not source_module:
            continue

        try:
            imports = extract_imports_from_file(
                path
            )

        except (
            SyntaxError,
            UnicodeDecodeError,
            OSError,
        ) as exc:
            try:
                relative = path.relative_to(
                    root_path
                )
            except ValueError:
                relative = path

            graph.errors.append(
                f"{relative}: {exc}"
            )

            graph.healthy = False
            continue

        for imported in imports:
            target: str | None = None

            # Exact internal module.
            if imported in module_by_name:
                target = imported

            else:
                imported_top = _top_level_module(
                    imported
                )

                # Look for an internal module/package.
                for module_name in module_by_name:
                    if (
                        module_name == imported_top
                        or module_name.startswith(
                            imported_top + "."
                        )
                    ):
                        target = module_name
                        break

            # Otherwise represent it as an external dependency.
            if target is None:
                target = imported

                graph.add_node(
                    target,
                    kind="external",
                )

            graph.add_edge(
                source_module,
                target,
                kind="imports",
            )

    _read_pyproject(
        root_path,
        graph,
    )

    return graph


def build_graph(
    root: str | Path,
) -> ProjectGraph:
    """Compatibility alias for build_project_graph."""
    return build_project_graph(root)


def analyze_project_graph(
    root: str | Path,
) -> dict:
    """Return project graph metrics."""
    graph = build_project_graph(root)

    internal_edges = [
        edge
        for edge in graph.edges
        if graph.nodes.get(edge.target)
        and graph.nodes[edge.target].kind == "source"
    ]

    external_edges = [
        edge
        for edge in graph.edges
        if (
            not graph.nodes.get(edge.target)
            or graph.nodes[edge.target].kind != "source"
        )
    ]

    source_count = sum(
        node.kind == "source"
        for node in graph.nodes.values()
    )

    project_count = sum(
        node.kind == "project"
        for node in graph.nodes.values()
    )

    external_dependency_count = sum(
        node.kind == "external"
        for node in graph.nodes.values()
    )

    return {
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "dependency_count": graph.dependency_count,
        "source_count": source_count,
        "project_count": project_count,
        "external_dependency_count": (
            external_dependency_count
        ),
        "internal_edge_count": len(
            internal_edges
        ),
        "external_edge_count": len(
            external_edges
        ),
        "isolated_node_count": len(
            graph.isolated_nodes()
        ),
        "errors": list(graph.errors),
        "healthy": graph.healthy,
        "graph": graph.to_dict(),
    }


def summarize_project_graph(
    graph: ProjectGraph,
) -> dict:
    """
    Return a compact summary of an existing ProjectGraph.

    This function is intentionally separate from
    analyze_project_graph so callers can analyze an
    already-built graph without rebuilding it.
    """
    source_count = sum(
        node.kind == "source"
        for node in graph.nodes.values()
    )

    project_count = sum(
        node.kind == "project"
        for node in graph.nodes.values()
    )

    external_dependency_count = sum(
        node.kind == "external"
        for node in graph.nodes.values()
    )

    dependencies = graph.dependencies()

    return {
        "file_count": source_count,
        "source_count": source_count,
        "dependency_count": len(dependencies),
        "dependencies": dependencies,
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "project_count": project_count,
        "external_dependency_count": (
            external_dependency_count
        ),
        "isolated_node_count": len(
            graph.isolated_nodes()
        ),
        "errors": list(graph.errors),
        "healthy": graph.healthy,
    }


def project_graph_summary(
    root: str | Path,
) -> str:
    """Return a human-readable project graph report."""
    analysis = analyze_project_graph(root)

    status = (
        "HEALTHY"
        if analysis["healthy"]
        else "UNHEALTHY"
    )

    return (
        "GEDT PROJECT GRAPH\n"
        "==================\n"
        f"Status: {status}\n"
        f"Source files: {analysis['source_count']}\n"
        f"Nodes: {analysis['node_count']}\n"
        f"Edges: {analysis['edge_count']}\n"
        f"Dependencies: {analysis['dependency_count']}\n"
        "External dependencies: "
        f"{analysis['external_dependency_count']}\n"
        "Isolated nodes: "
        f"{analysis['isolated_node_count']}"
    )


__all__ = [
    "ProjectNode",
    "ProjectEdge",
    "ProjectGraph",
    "extract_imports",
    "extract_imports_from_file",
    "build_project_graph",
    "build_graph",
    "analyze_project_graph",
    "summarize_project_graph",
    "project_graph_summary",
]