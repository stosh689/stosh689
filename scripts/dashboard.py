"""Matplotlib-based dashboard for visualizing open-data trends.

Builds a multi-panel figure (bar chart, scatter, heatmap) from World Bank
indicator data produced by ``worldbank_fetch`` and ``ai_analysis``.
"""

import matplotlib.pyplot as plt
import numpy as np


def build_dashboard(bar_df, scatter_df, corr_df, title="Open Data Dashboard"):
    """Build a 3-panel dashboard figure.

    Parameters
    ----------
    bar_df : DataFrame
        Single-indicator DataFrame for the bar chart (top countries).
    scatter_df : DataFrame
        Pivot table (country × indicator) for the scatter plot — uses the
        first two columns as x/y.
    corr_df : DataFrame
        Correlation matrix for the heatmap.

    Returns the ``matplotlib.figure.Figure``.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(title, fontsize=14)

    # --- Panel 1: bar chart (top countries) ---
    bar_value = [c for c in bar_df.columns if c not in ("Country", "Year")][0]
    top = bar_df.head(15)
    axes[0].barh(top["Country"], top[bar_value])
    axes[0].set_xlabel(bar_value)
    axes[0].set_title(f"Top Countries — {bar_value}")
    axes[0].invert_yaxis()

    # --- Panel 2: scatter (two indicators) ---
    cols = [c for c in scatter_df.columns]
    if len(cols) >= 2:
        data = scatter_df[[cols[0], cols[1]]].dropna()
        axes[1].scatter(data[cols[0]], data[cols[1]], alpha=0.6)
        axes[1].set_xlabel(cols[0])
        axes[1].set_ylabel(cols[1])
        axes[1].set_title(f"{cols[0]} vs {cols[1]}")
    else:
        axes[1].text(0.5, 0.5, "Not enough indicators for scatter",
                     ha="center", va="center", transform=axes[1].transAxes)

    # --- Panel 3: heatmap (correlation matrix) ---
    im = axes[2].imshow(corr_df.values, cmap="coolwarm", vmin=-1, vmax=1)
    axes[2].set_xticks(range(len(corr_df.columns)))
    axes[2].set_yticks(range(len(corr_df.index)))
    axes[2].set_xticklabels(corr_df.columns, rotation=45, ha="right")
    axes[2].set_yticklabels(corr_df.index)
    axes[2].set_title("Indicator Correlations")
    fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04)

    plt.tight_layout()
    return fig


def save_dashboard(fig, path, dpi=150):
    """Save *fig* to *path* and close it."""
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path
