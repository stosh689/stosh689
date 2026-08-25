from pathlib import Path

from gedt.project_graph import (
    ProjectGraph,
    build_project_graph,
    summarize_project_graph,
)


def test_project_graph_builds(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "import json\nimport pathlib\n",
        encoding="utf-8",
    )

    graph = build_project_graph(tmp_path)

    assert isinstance(graph, ProjectGraph)
    assert graph.node_count >= 3
    assert graph.edge_count >= 2
    assert "json" in graph.dependencies()
    assert "pathlib" in graph.dependencies()


def test_project_graph_detects_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "example"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.0",
    "numpy>=1.0",
]
""",
        encoding="utf-8",
    )

    graph = build_project_graph(tmp_path)

    assert "example" in {
        node.name
        for node in graph.nodes.values()
        if node.kind == "project"
    }

    assert "requests" in graph.dependencies()
    assert "numpy" in graph.dependencies()


def test_project_graph_handles_invalid_python(tmp_path: Path):
    (tmp_path / "broken.py").write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    graph = build_project_graph(tmp_path)

    assert graph.node_count >= 1
    assert graph.errors
    assert not graph.healthy


def test_project_graph_summary_is_deterministic(tmp_path: Path):
    (tmp_path / "main.py").write_text(
        "import json\n",
        encoding="utf-8",
    )

    graph = build_project_graph(tmp_path)
    summary = summarize_project_graph(graph)

    assert summary["file_count"] == 1
    assert summary["dependency_count"] == 1
    assert summary["dependencies"] == ["json"]
    assert summary["healthy"] is True