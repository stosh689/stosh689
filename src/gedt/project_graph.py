"""GEDT project dependency graph.
A lightweight, dependency-free graph analyzer for Python projects.
Compatible with Python 3.10+.
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
    """Representation of a GEDT project dependency graph."""
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
        """Add a node if it does not already exist."""
        if name not in self.nodes:
            self.nodes[name] = ProjectNode(
                name=name,
                path=str(path) if path is not None else None,
                kind=kind,
            )
        return self.nodes[name]
    def add_edge(
        self,
        source: str,
        target: str,
        kind: str = "imports",
    ) -> ProjectEdge:
        """Add a directed edge if it does not already exist."""
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
        """Return the number of graph nodes."""
        return len(self.nodes)
    @property
    def edge_count(self) -> int:
        """Return the number of graph edges."""
        return len(self.edges)
    @property
    def dependency_count(self) -> int:
        """Return the number of unique dependencies."""
        return len(self.dependencies())
    def dependencies(self) -> list[str]:
        """Return unique imported dependencies."""
        return sorted(
            {
                edge.target
                for edge in self.edges
                if edge.kind == "imports"
            }
        )
    def dependencies_of(self, name: str) -> list[str]:
        """Return dependencies imported by a node."""
        return sorted(
            {
                edge.target
                for edge in self.edges
                if edge.source == name
            }
        )
    def dependents_of(self, name: str) -> list[str]:
        """Return nodes that depend on a node."""
        return sorted(
            {
                edge.source
                for edge in self.edges
                if edge.target == name
            }
        )
    def has_node(self, name: str) -> bool:
        """Return whether a node exists."""
        return name in self.nodes
    def has_edge(
        self,
        source: str,
        target: str,
        kind: str = "imports",
    ) -> bool:
        """Return whether an edge exists."""
        return ProjectEdge(
            source=source,
            target=target,
            kind=kind,
        ) in self.edges
    def isolated_nodes(self) -> list[str]:
        """Return nodes that have no connections."""
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
    """Extract imported module names from Python source."""
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
def extract_imports_from_file(
    path: str | Path,
) -> list[str]:
    """Extract imports from a Python file."""
    return extract_imports(
        Path(path).read_text(encoding="utf-8")
    )
def _python_files(root: Path) -> Iterable[Path]:
    """Yield Python source files while skipping generated environments."""
    excluded = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "dist",
        "build",
    }
    for path in sorted(root.rglob("*.py")):
        if not path.is_file():
            continue
        if any(part in excluded for part in path.parts):
            continue
        yield path
def _module_name(
    root: Path,
    path: Path,
) -> str:
    """Convert a Python path into a dotted module name."""
    relative = path.relative_to(root)
    parts = list(relative.parts)
    if not parts:
        return ""
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)
def _dependency_name(value: str) -> str:
    """Normalize a dependency declaration."""
    value = value.strip()
    if "[" in value:
        value = value.split("[", 1)[0]
    for separator in (
        ">=",
        "<=",
        "==",
        "~=",
        "!=",
        ">",
        "<",
        ";",
    ):
        value = value.split(separator, 1)[0]
    return value.strip()
def _read_pyproject(
    root: Path,
    graph: ProjectGraph,
) -> None:
    """Add project metadata and declared dependencies."""
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
    name = project.get("name")
    if isinstance(name, str) and name.strip():
        graph.add_node(
            name.strip(),
            pyproject,
            "project",
        )
    dependencies = project.get(
        "dependencies",
        [],
    )
    if isinstance(dependencies, list):
        for dependency in dependencies:
            if not isinstance(dependency, str):
                continue
            package = _dependency_name(dependency)
            if package:
                graph.add_node(
                    package,
                    kind="external",
                )
def build_project_graph(
    root: str | Path,
) -> ProjectGraph:
    """Build a dependency graph for a Python project."""
    root_path = Path(root).resolve()
    graph = ProjectGraph()
    files = list(
        _python_files(root_path)
    )
    modules: dict[str, Path] = {}
    # First pass: register source modules.
    for path in files:
        module = _module_name(
            root_path,
            path,
        )
        if not module:
            continue
        modules[module] = path
        graph.add_node(
            module,
            path,
            "source",
        )
    # Second pass: resolve imports.
    for path in files:
        source = _module_name(
            root_path,
            path,
        )
        if not source:
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
            graph.errors.append(
                f"{path.relative_to(root_path)}: {exc}"
            )
            graph.healthy = False
            continue
        for imported in imports:
            target: str | None = None
            if imported in modules:
                target = imported
            else:
                top_level = imported.split(
                    ".",
                    1,
                )[0]
                matches = sorted(
                    module
                    for module in modules
                    if module == top_level
                    or module.startswith(
                        top_level + "."
                    )
                )
                if matches:
                    target = matches[0]
            if target is None:
                target = imported
            if target not in graph.nodes:
                graph.add_node(
                    target,
                    kind="external",
                )
            graph.add_edge(
                source,
                target,
            )
    # Add pyproject metadata.
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
def summarize_project_graph(
    graph: ProjectGraph,
) -> dict:
    """Return useful project graph statistics."""
    source_count = sum(
        node.kind == "source"
        for node in graph.nodes.values()
    )
    project_count = sum(
        node.kind == "project"
        for node in graph.nodes.values()
    )
    external_count = sum(
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
        "external_dependency_count": external_count,
        "isolated_node_count": len(
            graph.isolated_nodes()
        ),
        "errors": list(graph.errors),
        "healthy": graph.healthy,
    }
def analyze_project_graph(
    root: str | Path,
) -> dict:
    """Build and analyze the project graph."""
    graph = build_project_graph(root)
    result = summarize_project_graph(
        graph
    )
    internal_edge_count = 0
    for edge in graph.edges:
        target = graph.nodes.get(
            edge.target
        )
        if target is not None and target.kind == "source":
            internal_edge_count += 1
    result["internal_edge_count"] = (
        internal_edge_count
    )
    result["external_edge_count"] = (
        graph.edge_count
        - internal_edge_count
    )
    result["graph"] = graph.to_dict()
    return result
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
    return "\n".join(
        [
            "GEDT PROJECT GRAPH",
            "==================",
            f"Status: {status}",
            f"Source files: {analysis['source_count']}",
            f"Nodes: {analysis['node_count']}",
            f"Edges: {analysis['edge_count']}",
            f"Dependencies: {analysis['dependency_count']}",
            (
                "External dependencies: "
                f"{analysis['external_dependency_count']}"
            ),
            (
                "Isolated nodes: "
                f"{analysis['isolated_node_count']}"
            ),
        ]
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