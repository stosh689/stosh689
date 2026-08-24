"""
GEDT compatibility layer for crisis-management ML functionality.
This module provides the train_ml_model() function expected by
ml_model.py and GEDT smoke tests.
The implementation intentionally stays lightweight so it does not
interfere with the existing CIDAR/GEDT architecture.
"""
from __future__ import annotations
from typing import Any
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
def train_ml_model(
    X: Any,
    y: Any,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """
    Train a small, deterministic classification model.
    Parameters
    ----------
    X:
        Feature matrix.
    y:
        Target labels.
    test_size:
        Fraction of data reserved for testing.
    random_state:
        Random seed for reproducibility.
    Returns
    -------
    dict
        A model bundle containing the trained model and data splits.
    """
    X_array = np.asarray(X)
    y_array = np.asarray(y)
    if len(X_array) != len(y_array):
        raise ValueError("X and y must contain the same number of samples.")
    if len(X_array) < 2:
        raise ValueError("At least two samples are required.")
    X_train, X_test, y_train, y_test = train_test_split(
        X_array,
        y_array,
        test_size=test_size,
        random_state=random_state,
    )
    model = RandomForestClassifier(
        n_estimators=50,
        random_state=random_state,
    )
    model.fit(X_train, y_train)
    return {
        "model": model,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
    }
__all__ = ["train_ml_model"]