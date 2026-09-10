"""Regression tests for the canonical GEDT package layout."""

from gedt.cidar_runner import CIDARRunResult, run_arrays
from gedt.project_graph import ProjectGraph, build_project_graph


def test_cidar_runner_imports_from_canonical_package():
    assert CIDARRunResult is not None
    assert callable(run_arrays)


def test_project_graph_imports_from_canonical_package():
    assert ProjectGraph is not None
    assert callable(build_project_graph)