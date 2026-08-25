"""
GEDT Project Graph
A lightweight dependency/project graph for analyzing Python projects.
This module is intentionally self-contained so it can be added to GEDT
without changing existing modules.
The graph records:
- Python source files
- imported modules
- internal project dependencies
- external dependencies
- dependency relationships
- simple project-level metrics
No third-party packages are required.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
@dataclass(frozen=True)
class ProjectNode:
    """A node representing a project file or dependency."""
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
    """Directed graph representing project dependencies."""
    nodes: dict[str, ProjectNode] = field(default_factory=dict)
    edges: list[ProjectEdge] = field(default_factory=list)
    def add_node(
        self,
        name: str,
        path: str | Path | None = None,
        kind: str = "module",
    ) -> ProjectNode:
        """Add a node if it does not already exist."""
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
        """Add a directed edge between two nodes."""
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
        """Return the number of dependency relationships."""
        return len(self.edges)
    def dependencies_of(self, name: str) -> list[str]:
        """Return nodes directly imported by a node."""
        return [
            edge.target
            for edge in self.edges
            if edge.source == name
        ]
    def dependents_of(self, name: str) -> list[str]:
        """Return nodes that depend on a node."""
        return [
            edge.source
            for edge in self.edges
            if edge.target == name
        ]
    def has_node(self, name: str) -> bool:
        """Return whether a node exists."""
        return name in self.nodes
    def has_edge(
        self,
        source: str,
        target: str,
        kind: str = "imports",
    ) -> bool:
        """Return whether a relationship exists."""
        return ProjectEdge(source, target, kind) in self.edges
    def isolated_nodes(self) -> list[str]:
        """Return nodes with no incoming or outgoing relationships."""
        connected: set[str] = set()
        for edge in self.edges:
            connected.add(edge.source)
            connected.add(edge.target)
        return [
            name
            for name in self.nodes
            if name not in connected
        ]
    def to_dict(self) -> dict:
        """Return a JSON-friendly representation."""
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
        }
def extract_imports(source: str) -> list[str]:
    """
    Extract imported module names from Python source code.
    Both ``import x`` and ``from x import y`` forms are supported.
    """
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return sorted(set(imports))
def extract_imports_from_file(path: str | Path) -> list[str]:
    """Read a Python file and extract its imports."""
    file_path = Path(path)
    source = file_path.read_text(encoding="utf-8")
    return extract_imports(source)
def _python_files(root: Path) -> Iterable[Path]:
    """Yield Python source files below a project root."""
    excluded = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
    }
    for path in root.rglob("*.py"):
        if any(part in excluded for part in path.parts):
            continue
        if path.is_file():
            yield path
def _module_name(root: Path, path: Path) -> str:
    """
    Convert a Python file path into a reasonable module name.
    """
    relative = path.relative_to(root)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)
def _top_level_module(import_name: str) -> str:
    """Return the top-level portion of an import."""
    return import_name.split(".", 1)[0]
def build_project_graph(
    root: str | Path,
) -> ProjectGraph:
    """
    Build a dependency graph from Python files beneath ``root``.
    Internal imports are connected to project nodes when possible.
    External imports are represented as dependency nodes.
    """
    root_path = Path(root).resolve()
    graph = ProjectGraph()
    files = list(_python_files(root_path))
    module_by_name: dict[str, Path] = {}
    for path in files:
        module = _module_name(root_path, path)
        module_by_name[module] = path
        graph.add_node(
            module,
            path=path,
            kind="source",
        )
    for path in files:
        source_module = _module_name(root_path, path)
        try:
            imports = extract_imports_from_file(path)
        except (SyntaxError, UnicodeDecodeError):
            # A malformed source file should not prevent the rest of
            # the project graph from being constructed.
            continue
        for imported in imports:
            imported_top = _top_level_module(imported)
            target = None
            if imported in module_by_name:
                target = imported
            else:
                for module_name in module_by_name:
                    if (
                        module_name == imported_top
                        or module_name.startswith(imported_top + ".")
                    ):
                        target = module_name
                        break
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
    return graph
def build_graph(root: str | Path) -> ProjectGraph:
    """Compatibility alias for ``build_project_graph``."""
    return build_project_graph(root)
def analyze_project_graph(
    root: str | Path,
) -> dict:
    """
    Build a graph and return useful project-level metrics.
    """
    graph = build_project_graph(root)
    internal_edges = [
        edge
        for edge in graph.edges
        if graph.nodes.get(edge.target, ProjectNode("", kind="external")).kind
        == "source"
    ]
    external_edges = [
        edge
        for edge in graph.edges
        if graph.nodes.get(edge.target, ProjectNode("", kind="external")).kind
        != "source"
    ]
    return {
        "node_count": graph.node_count,
        "edge_count": graph.edge_count,
        "dependency_count": graph.dependency_count,
        "source_count": sum(
            node.kind == "source"
            for node in graph.nodes.values()
        ),
        "external_dependency_count": sum(
            node.kind == "external"
            for node in graph.nodes.values()
        ),
        "internal_edge_count": len(internal_edges),
        "external_edge_count": len(external_edges),
        "isolated_node_count": len(graph.isolated_nodes()),
        "graph": graph.to_dict(),
    }
def project_graph_summary(root: str | Path) -> str:
    """Return a human-readable graph summary."""
    analysis = analyze_project_graph(root)
    return (
        "GEDT PROJECT GRAPH\n"
        "==================\n"
        f"Source files: {analysis['source_count']}\n"
        f"Nodes: {analysis['node_count']}\n"
        f"Edges: {analysis['edge_count']}\n"
        f"Dependencies: {analysis['dependency_count']}\n"
        f"External dependencies: "
        f"{analysis['external_dependency_count']}\n"
        f"Isolated nodes: {analysis['isolated_node_count']}"
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
    "project_graph_summary",
]