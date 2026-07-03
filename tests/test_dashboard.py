"""Tests for scripts/dashboard.py."""

import pandas as pd

from scripts import dashboard


def _bar_df():
    return pd.DataFrame({
        "Country": ["A", "B", "C"],
        "Year": ["2020", "2020", "2020"],
        "Value": [100.0, 50.0, 10.0],
    })


def _scatter_df():
    return pd.DataFrame({
        "Energy Use": [100.0, 50.0, 10.0],
        "CO2 Emissions": [5.0, 3.0, 1.0],
    }, index=["A", "B", "C"])


def _corr_df():
    return pd.DataFrame({
        "Energy Use": [1.0, 0.9, 0.8],
        "CO2 Emissions": [0.9, 1.0, 0.7],
        "GDP": [0.8, 0.7, 1.0],
    }, index=["Energy Use", "CO2 Emissions", "GDP"])


def test_build_dashboard_returns_figure():
    fig = dashboard.build_dashboard(_bar_df(), _scatter_df(), _corr_df())
    assert fig is not None
    # 3 panels + 1 colorbar axis
    assert len(fig.axes) == 4
    plt_close(fig)


def test_save_dashboard(tmp_path):
    fig = dashboard.build_dashboard(_bar_df(), _scatter_df(), _corr_df())
    path = tmp_path / "dash.png"
    result = dashboard.save_dashboard(fig, str(path))
    assert result == str(path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_build_dashboard_single_indicator_scatter():
    """Scatter panel handles < 2 columns gracefully."""
    scatter = pd.DataFrame({"Only One": [1.0, 2.0]}, index=["A", "B"])
    fig = dashboard.build_dashboard(_bar_df(), scatter, _corr_df())
    assert fig is not None
    plt_close(fig)


def plt_close(fig):
    import matplotlib.pyplot as plt
    plt.close(fig)
