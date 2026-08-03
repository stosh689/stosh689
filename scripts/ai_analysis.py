"""AI-based analysis of World Bank indicator datasets.

Uses scikit-learn for clustering, trend detection, and correlation analysis.
All functions operate on pandas DataFrames produced by ``worldbank_fetch``.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression


def cluster_countries(df, n_clusters=3, feature_col=None):
    """Cluster countries into *n_clusters* groups using KMeans.

    *df* is a single-indicator DataFrame (output of ``process_data``) or a
    pivot table (output of ``compare_indicators``).  Returns a Series mapping
    country -> cluster label.
    """
    if feature_col is None:
        feature_col = [c for c in df.columns if c not in (
            "Country", "Year")][0]

    data = df[[feature_col]].dropna()
    if len(data) < n_clusters:
        raise ValueError(
            f"Not enough data points ({len(data)}) for {n_clusters} clusters"
        )

    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(data)
    return pd.Series(labels, index=data.index, name="cluster")


def detect_trends(df, value_col=None):
    """Detect the linear trend (slope) of an indicator over time per country.

    *df* must contain ``Country``, ``Year``, and a value column.
    Returns a Series mapping country -> slope (units per year).
    """
    if value_col is None:
        value_col = [c for c in df.columns if c not in ("Country", "Year")][0]

    slopes = {}
    for country, group in df.groupby("Country"):
        group = group.dropna(subset=[value_col]).sort_values("Year")
        if len(group) < 2:
            continue
        x = group["Year"].astype(float).values.reshape(-1, 1)
        y = group[value_col].astype(float).values
        model = LinearRegression()
        model.fit(x, y)
        slopes[country] = float(model.coef_[0])
    return pd.Series(slopes, name="trend_slope")


def correlation_matrix(pivot_df):
    """Compute the pairwise correlation matrix between indicators.

    *pivot_df* is a country × indicator DataFrame (output of
    ``compare_indicators``).  Returns a DataFrame of Pearson correlations.
    """
    return pivot_df.corr(method="pearson")


def summarize(pivot_df, n_clusters=3):
    """Run a full analysis pipeline on a pivot table.

    Returns a dict with ``clusters``, ``correlations``.
    """
    return {
        "clusters": cluster_countries(pivot_df, n_clusters=n_clusters),
        "correlations": correlation_matrix(pivot_df),
    }
