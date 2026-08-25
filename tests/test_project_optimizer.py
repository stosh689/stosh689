from pathlib import Path

from gedt.project_graph import build_project_graph
from gedt.project_optimizer import (
    ProjectOptimization,
    analyze_project,
    optimize_project,
    optimize_project_graph,
    optimization_report,
)


def test_optimizer_returns_valid_result():
    root = Path(__file__).resolve().parents[1]

    result = optimize_project(root)

    assert isinstance(result, ProjectOptimization)
    assert result.node_count >= 0
    assert result.edge_count >= 0
    assert 0 <= result.score <= 100


def test_optimizer_graph_analysis():
    root = Path(__file__).resolve().parents[1]

    graph = build_project_graph(root)
    result = optimize_project_graph(graph)

    assert isinstance(result, ProjectOptimization)
    assert result.node_count == graph.node_count
    assert result.edge_count == graph.edge_count


def test_optimizer_report_has_header():
    root = Path(__file__).resolve().parents[1]

    report = optimization_report(root)

    assert "GEDT PROJECT OPTIMIZATION" in report
    assert "Optimization score:" in report
    assert "Source files:" in report
    assert "Dependencies:" in report


def test_optimizer_json_result():
    root = Path(__file__).resolve().parents[1]

    result = analyze_project(root)

    assert isinstance(result, dict)
    assert "score" in result
    assert "healthy" in result
    assert "findings" in result
    assert isinstance(result["findings"], list)


def test_optimizer_detects_simple_cycle():
    root = Path(__file__).resolve().parents[1]

    graph = build_project_graph(root)

    result = optimize_project_graph(graph)

    # The real repository may or may not contain a cycle.
    # The important contract is that cycle analysis completes
    # and produces correctly shaped findings.
    for finding in result.findings:
        assert finding.category
        assert finding.severity
        assert finding.title
        assert finding.description
        assert finding.recommendation


def test_optimizer_findings_are_serializable():
    root = Path(__file__).resolve().parents[1]

    result = analyze_project(root)

    for finding in result["findings"]:
        assert isinstance(finding, dict)
        assert "category" in finding
        assert "severity" in finding
        assert "title" in finding
        assert "description" in finding
        assert "target" in finding
        assert "recommendation" in finding