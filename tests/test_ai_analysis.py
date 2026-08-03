"""Tests for scripts/ai_analysis.py."""

import numpy as np
import pandas as pd
import pytest

from scripts import ai_analysis


def _single_indicator_df():
    """Country × Year × Value DataFrame."""
    return pd.DataFrame({
        "Country": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
        "Year": [2018, 2019, 2020, 2018, 2019, 2020, 2018, 2019, 2020],
        "Value": [10.0, 12.0, 14.0, 50.0, 55.0, 60.0, 100.0, 110.0, 120.0],
    })


def _pivot_df():
    """Country × indicator pivot table."""
    return pd.DataFrame({
        "Energy Use": [100.0, 50.0, 10.0],
        "CO2 Emissions": [5.0, 3.0, 1.0],
        "GDP per Capita": [30000.0, 15000.0, 5000.0],
    }, index=["A", "B", "C"])


# --- cluster_countries ---
def test_cluster_countries_returns_labels():
    df = _single_indicator_df()
    labels = ai_analysis.cluster_countries(df, n_clusters=3)
    assert len(labels) == 9  # 3 countries × 3 years
    assert set(labels.unique()) == {0, 1, 2}


def test_cluster_countries_pivot():
    pivot = _pivot_df()
    labels = ai_analysis.cluster_countries(pivot, n_clusters=2)
    assert len(labels) == 3
    # country A (high) and C (low) should be in different clusters
    assert labels["A"] != labels["C"]


def test_cluster_countries_too_few_points():
    df = pd.DataFrame({"Country": ["A"], "Year": [2020], "Value": [1.0]})
    with pytest.raises(ValueError, match="Not enough data points"):
        ai_analysis.cluster_countries(df, n_clusters=3)


# --- detect_trends ---
def test_detect_trends_positive_slope():
    df = _single_indicator_df()
    slopes = ai_analysis.detect_trends(df)
    assert len(slopes) == 3
    # all trends positive (values increase over years)
    assert all(s > 0 for s in slopes.values)


def test_detect_trends_negative_slope():
    df = pd.DataFrame({
        "Country": ["A", "A", "A"],
        "Year": [2018, 2019, 2020],
        "Value": [100.0, 80.0, 60.0],
    })
    slopes = ai_analysis.detect_trends(df)
    assert slopes["A"] < 0


def test_detect_trends_skips_single_point():
    df = pd.DataFrame({
        "Country": ["A", "B"],
        "Year": [2020, 2020],
        "Value": [1.0, 2.0],
    })
    slopes = ai_analysis.detect_trends(df)
    assert len(slopes) == 0  # each country has only 1 point


# --- correlation_matrix ---
def test_correlation_matrix_shape():
    pivot = _pivot_df()
    corr = ai_analysis.correlation_matrix(pivot)
    assert corr.shape == (3, 3)
    # diagonal = 1
    assert all(np.isclose(np.diag(corr), 1.0))


def test_correlation_matrix_perfect():
    pivot = pd.DataFrame({
        "A": [1.0, 2.0, 3.0],
        "B": [2.0, 4.0, 6.0],  # perfect positive correlation
    })
    corr = ai_analysis.correlation_matrix(pivot)
    assert np.isclose(corr.loc["A", "B"], 1.0)


# --- summarize ---
def test_summarize():
    pivot = _pivot_df()
    result = ai_analysis.summarize(pivot, n_clusters=2)
    assert "clusters" in result
    assert "correlations" in result
    assert len(result["clusters"]) == 3
    assert result["correlations"].shape == (3, 3)
