"""
Global Digital Twin — Gate 8
Calibration & Parameter Estimation Engine

Purpose
-------
Gate 8 adds parameter calibration to the Global Digital Twin framework.

It provides:

1. Parameter registry with bounded search spaces.
2. Synthetic demonstration observations with known parameters.
3. Time-ordered train/test separation.
4. Deterministic coordinate-search calibration.
5. RMSE / MAE / bias / correlation / directional accuracy.
6. Before-vs-after calibration evaluation.
7. Holdout testing to reduce overfitting risk.
8. One-at-a-time parameter sensitivity analysis.
9. Complexity-aware objective scoring.
10. Deterministic fingerprints.
11. JSON and CSV export.
12. Standard-library-only implementation.
13. Self-tests.
14. Command-line interface.

IMPORTANT SCIENTIFIC NOTE
-------------------------
The default demonstration data are synthetic.

Successful calibration on synthetic data demonstrates that the
calibration machinery works. It is NOT evidence that the Global
Digital Twin is empirically validated.

For scientific use, replace the demonstration data with properly
sourced historical observations and document:

- source
- units
- geographic coverage
- temporal coverage
- preprocessing
- missing-data handling
- uncertainty
- revision policy
- train/test period
- parameter constraints

License
-------
MIT-style project prototype for 123 Inc.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass(frozen=True)
class Parameter:
    """A calibratable model parameter."""

    name: str
    default: float
    lower: float
    upper: float
    step: float
    description: str

    def values(self) -> List[float]:
        """Return the bounded deterministic search grid."""
        if self.step <= 0:
            raise ValueError(f"Parameter step must be positive: {self.name}")

        values: List[float] = []
        current = self.lower

        # Numerical tolerance prevents floating-point drift.
        while current <= self.upper + (self.step * 1e-9):
            values.append(round(current, 10))
            current += self.step

        # Guarantee upper boundary is represented.
        if not values or values[-1] < self.upper - (self.step * 1e-9):
            values.append(round(self.upper, 10))

        return sorted(set(values))


@dataclass
class Observation:
    """One time-indexed observation."""

    period: int
    economic_signal: float
    climate_risk: float
    food_security: float
    energy_reliability: float
    resilience: float
    governance: float
    observed_score: float
    domain: str = "global"


@dataclass
class Metrics:
    """Prediction-quality metrics."""

    count: int
    mae: float
    rmse: float
    bias: float
    correlation: float
    directional_accuracy: float
    normalized_rmse: float
    validation_score: float


@dataclass
class CalibrationResult:
    """Complete Gate 8 calibration result."""

    initial_parameters: Dict[str, float]
    calibrated_parameters: Dict[str, float]

    training_before: Metrics
    training_after: Metrics

    test_before: Metrics
    test_after: Metrics

    objective_before: float
    objective_after: float

    improvement_training_percent: float
    improvement_test_percent: float

    sensitivity: Dict[str, Dict[str, float]]

    fingerprint: str
    synthetic_demo: bool


# ============================================================================
# PARAMETER REGISTRY
# ============================================================================

def default_parameter_registry() -> List[Parameter]:
    """
    Define the model's calibratable parameters.

    The parameters are intentionally interpretable rather than opaque.
    """

    return [
        Parameter(
            name="intercept",
            default=50.0,
            lower=40.0,
            upper=60.0,
            step=2.0,
            description="Baseline global score.",
        ),
        Parameter(
            name="economic_weight",
            default=8.0,
            lower=4.0,
            upper=12.0,
            step=1.0,
            description="Contribution of economic conditions.",
        ),
        Parameter(
            name="climate_weight",
            default=10.0,
            lower=5.0,
            upper=15.0,
            step=1.0,
            description="Penalty associated with climate risk.",
        ),
        Parameter(
            name="food_weight",
            default=8.0,
            lower=4.0,
            upper=12.0,
            step=1.0,
            description="Contribution of food security.",
        ),
        Parameter(
            name="energy_weight",
            default=7.0,
            lower=3.0,
            upper=11.0,
            step=1.0,
            description="Contribution of energy reliability.",
        ),
        Parameter(
            name="resilience_weight",
            default=9.0,
            lower=4.0,
            upper=14.0,
            step=1.0,
            description="Contribution of resilience.",
        ),
        Parameter(
            name="governance_weight",
            default=8.0,
            lower=4.0,
            upper=12.0,
            step=1.0,
            description="Contribution of governance.",
        ),
    ]


# ============================================================================
# MODEL
# ============================================================================

def predict(
    observation: Observation,
    parameters: Dict[str, float],
) -> float:
    """
    Predict the global score.

    Signals are represented on approximately a 0–1 scale.

    Climate risk is a negative contribution:
        higher climate risk -> lower global score.

    Other signals are positive contributions.
    """

    value = parameters["intercept"]

    value += parameters["economic_weight"] * observation.economic_signal
    value -= parameters["climate_weight"] * observation.climate_risk
    value += parameters["food_weight"] * observation.food_security
    value += parameters["energy_weight"] * observation.energy_reliability
    value += parameters["resilience_weight"] * observation.resilience
    value += parameters["governance_weight"] * observation.governance

    return value


def predict_series(
    observations: Sequence[Observation],
    parameters: Dict[str, float],
) -> List[float]:
    """Predict an entire observation series."""
    return [predict(item, parameters) for item in observations]


# ============================================================================
# METRICS
# ============================================================================

def _safe_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return statistics.mean(values)


def mean_absolute_error(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> float:
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lengths must match.")

    if not actual:
        return 0.0

    return statistics.mean(
        abs(a - p)
        for a, p in zip(actual, predicted)
    )


def root_mean_squared_error(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> float:
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lengths must match.")

    if not actual:
        return 0.0

    return math.sqrt(
        statistics.mean(
            (a - p) ** 2
            for a, p in zip(actual, predicted)
        )
    )


def bias(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> float:
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lengths must match.")

    if not actual:
        return 0.0

    return statistics.mean(
        p - a
        for a, p in zip(actual, predicted)
    )


def correlation(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> float:
    """
    Pearson correlation.

    Returns 0 when correlation cannot be meaningfully calculated.
    """

    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lengths must match.")

    if len(actual) < 2:
        return 0.0

    mean_actual = statistics.mean(actual)
    mean_predicted = statistics.mean(predicted)

    numerator = sum(
        (a - mean_actual) * (p - mean_predicted)
        for a, p in zip(actual, predicted)
    )

    denominator_a = math.sqrt(
        sum((a - mean_actual) ** 2 for a in actual)
    )

    denominator_p = math.sqrt(
        sum((p - mean_predicted) ** 2 for p in predicted)
    )

    denominator = denominator_a * denominator_p

    if denominator == 0:
        return 0.0

    return numerator / denominator


def directional_accuracy(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> float:
    """
    Compare direction of period-to-period changes.

    The first period has no direction and is therefore excluded.
    """

    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lengths must match.")

    if len(actual) < 2:
        return 0.0

    correct = 0
    total = 0

    for index in range(1, len(actual)):
        actual_change = actual[index] - actual[index - 1]
        predicted_change = predicted[index] - predicted[index - 1]

        actual_direction = (
            1 if actual_change > 0
            else -1 if actual_change < 0
            else 0
        )

        predicted_direction = (
            1 if predicted_change > 0
            else -1 if predicted_change < 0
            else 0
        )

        if actual_direction == predicted_direction:
            correct += 1

        total += 1

    return correct / total if total else 0.0


def calculate_metrics(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> Metrics:
    """Calculate the complete Gate 8 validation metric set."""

    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lengths must match.")

    if not actual:
        return Metrics(
            count=0,
            mae=0.0,
            rmse=0.0,
            bias=0.0,
            correlation=0.0,
            directional_accuracy=0.0,
            normalized_rmse=0.0,
            validation_score=0.0,
        )

    mae = mean_absolute_error(actual, predicted)
    rmse = root_mean_squared_error(actual, predicted)
    prediction_bias = bias(actual, predicted)
    corr = correlation(actual, predicted)
    direction = directional_accuracy(actual, predicted)

    observed_range = max(actual) - min(actual)

    if observed_range == 0:
        normalized_rmse = rmse
    else:
        normalized_rmse = rmse / observed_range

    # A bounded 0–100 validation score.
    #
    # This is a summary metric, not a replacement for the individual
    # scientific statistics above.
    error_component = max(0.0, 1.0 - normalized_rmse)
    correlation_component = max(0.0, min(1.0, (corr + 1.0) / 2.0))
    direction_component = max(0.0, min(1.0, direction))

    validation_score = 100.0 * (
        0.50 * error_component
        + 0.30 * correlation_component
        + 0.20 * direction_component
    )

    return Metrics(
        count=len(actual),
        mae=mae,
        rmse=rmse,
        bias=prediction_bias,
        correlation=corr,
        directional_accuracy=direction,
        normalized_rmse=normalized_rmse,
        validation_score=validation_score,
    )


# ============================================================================
# DATA GENERATION
# ============================================================================

def generate_synthetic_observations(
    periods: int = 60,
    seed: int = 42,
) -> Tuple[List[Observation], Dict[str, float]]:
    """
    Generate a deterministic synthetic dataset.

    The returned second value contains the hidden parameters used to
    generate the observations.

    This exists specifically to test whether the calibration engine can
    recover a plausible parameter configuration.
    """

    if periods < 10:
        raise ValueError("At least 10 periods are required.")

    rng = random.Random(seed)

    true_parameters = {
        "intercept": 52.0,
        "economic_weight": 9.0,
        "climate_weight": 11.0,
        "food_weight": 7.0,
        "energy_weight": 8.0,
        "resilience_weight": 10.0,
        "governance_weight": 6.0,
    }

    observations: List[Observation] = []

    for period in range(periods):
        trend = period / max(1, periods - 1)

        economic = min(
            1.0,
            max(
                0.0,
                0.48 + 0.25 * trend
                + 0.07 * math.sin(period / 5.0)
                + rng.gauss(0.0, 0.025),
            ),
        )

        climate = min(
            1.0,
            max(
                0.0,
                0.30 + 0.25 * trend
                + 0.08 * math.sin(period / 7.0)
                + rng.gauss(0.0, 0.025),
            ),
        )

        food = min(
            1.0,
            max(
                0.0,
                0.62 - 0.10 * trend
                + 0.05 * math.cos(period / 4.0)
                + rng.gauss(0.0, 0.02),
            ),
        )

        energy = min(
            1.0,
            max(
                0.0,
                0.55 + 0.20 * trend
                + 0.06 * math.sin(period / 6.0)
                + rng.gauss(0.0, 0.02),
            ),
        )

        resilience = min(
            1.0,
            max(
                0.0,
                0.50 + 0.18 * trend
                + 0.05 * math.cos(period / 5.0)
                + rng.gauss(0.0, 0.02),
            ),
        )

        governance = min(
            1.0,
            max(
                0.0,
                0.58 + 0.10 * trend
                + 0.04 * math.sin(period / 8.0)
                + rng.gauss(0.0, 0.018),
            ),
        )

        base_observation = Observation(
            period=period,
            economic_signal=economic,
            climate_risk=climate,
            food_security=food,
            energy_reliability=energy,
            resilience=resilience,
            governance=governance,
            observed_score=0.0,
        )

        true_score = predict(
            base_observation,
            true_parameters,
        )

        noisy_score = true_score + rng.gauss(0.0, 0.45)

        observations.append(
            Observation(
                period=period,
                economic_signal=economic,
                climate_risk=climate,
                food_security=food,
                energy_reliability=energy,
                resilience=resilience,
                governance=governance,
                observed_score=noisy_score,
            )
        )

    return observations, true_parameters


# ============================================================================
# CSV INPUT
# ============================================================================

REQUIRED_CSV_COLUMNS = [
    "period",
    "economic_signal",
    "climate_risk",
    "food_security",
    "energy_reliability",
    "resilience",
    "governance",
    "observed_score",
]


def load_observations_csv(
    filename: str,
) -> List[Observation]:
    """
    Load observations from CSV.

    Required columns are listed in REQUIRED_CSV_COLUMNS.
    """

    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {filename}")

    observations: List[Observation] = []

    with path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError("CSV has no header.")

        missing = [
            column
            for column in REQUIRED_CSV_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(missing)
            )

        for row in reader:
            observations.append(
                Observation(
                    period=int(row["period"]),
                    economic_signal=float(row["economic_signal"]),
                    climate_risk=float(row["climate_risk"]),
                    food_security=float(row["food_security"]),
                    energy_reliability=float(row["energy_reliability"]),
                    resilience=float(row["resilience"]),
                    governance=float(row["governance"]),
                    observed_score=float(row["observed_score"]),
                    domain=row.get("domain", "global") or "global",
                )
            )

    observations.sort(key=lambda item: item.period)

    if len(observations) < 10:
        raise ValueError(
            "At least 10 observations are required for calibration."
        )

    return observations


# ============================================================================
# TRAIN / TEST SPLIT
# ============================================================================

def chronological_split(
    observations: Sequence[Observation],
    train_periods: int,
) -> Tuple[List[Observation], List[Observation]]:
    """
    Split observations chronologically.

    No random shuffling is used.

    This is important for time-dependent systems because future data
    should not leak into model calibration.
    """

    ordered = sorted(
        observations,
        key=lambda item: item.period,
    )

    if train_periods < 2:
        raise ValueError("train_periods must be at least 2.")

    if train_periods >= len(ordered):
        raise ValueError(
            "train_periods must leave at least two holdout observations."
        )

    return (
        ordered[:train_periods],
        ordered[train_periods:],
    )


# ============================================================================
# OBJECTIVE FUNCTION
# ============================================================================

def objective(
    observations: Sequence[Observation],
    parameters: Dict[str, float],
    complexity_penalty: float = 0.0,
) -> float:
    """
    Calibration objective.

    Primary objective:
        RMSE

    Optional complexity penalty:
        discourages unnecessary parameter movement away from defaults.

    The default penalty is zero because the demonstration model has a
    fixed interpretable structure.
    """

    if not observations:
        return float("inf")

    predicted = predict_series(
        observations,
        parameters,
    )

    actual = [
        item.observed_score
        for item in observations
    ]

    rmse = root_mean_squared_error(
        actual,
        predicted,
    )

    penalty = complexity_penalty * sum(
        abs(value)
        for value in parameters.values()
    )

    return rmse + penalty


# ============================================================================
# CALIBRATION ENGINE
# ============================================================================

class CalibrationEngine:
    """
    Deterministic coordinate-search calibration engine.

    Each parameter is tested over its bounded grid while all other
    parameters remain fixed.

    Multiple passes allow parameters to interact without creating a
    combinatorial full-grid explosion.
    """

    def __init__(
        self,
        registry: Sequence[Parameter],
        complexity_penalty: float = 0.0,
    ) -> None:
        self.registry = list(registry)
        self.complexity_penalty = complexity_penalty

        if not self.registry:
            raise ValueError("Parameter registry cannot be empty.")

    def default_parameters(self) -> Dict[str, float]:
        return {
            parameter.name: parameter.default
            for parameter in self.registry
        }

    def clamp_parameters(
        self,
        parameters: Dict[str, float],
    ) -> Dict[str, float]:
        """Ensure parameters remain inside declared bounds."""

        result = dict(parameters)

        for parameter in self.registry:
            value = result.get(
                parameter.name,
                parameter.default,
            )

            result[parameter.name] = min(
                parameter.upper,
                max(parameter.lower, value),
            )

        return result

    def calibrate(
        self,
        observations: Sequence[Observation],
        passes: int = 3,
    ) -> Dict[str, float]:
        """
        Calibrate parameters using deterministic coordinate search.
        """

        if len(observations) < 2:
            raise ValueError(
                "At least two observations are required."
            )

        if passes < 1:
            raise ValueError("passes must be at least 1.")

        current = self.default_parameters()

        current_score = objective(
            observations,
            current,
            self.complexity_penalty,
        )

        for _ in range(passes):
            changed = False

            for parameter in self.registry:
                best_value = current[parameter.name]
                best_score = current_score

                for candidate in parameter.values():
                    trial = dict(current)
                    trial[parameter.name] = candidate

                    trial_score = objective(
                        observations,
                        trial,
                        self.complexity_penalty,
                    )

                    # Deterministic tie-breaking:
                    # keep the existing value when scores are equal.
                    if trial_score < best_score - 1e-12:
                        best_score = trial_score
                        best_value = candidate

                if best_value != current[parameter.name]:
                    current[parameter.name] = best_value
                    current_score = best_score
                    changed = True

            if not changed:
                break

        return self.clamp_parameters(current)


# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================

def parameter_sensitivity(
    observations: Sequence[Observation],
    calibrated_parameters: Dict[str, float],
    registry: Sequence[Parameter],
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate local sensitivity around each calibrated parameter.

    For each parameter:

        lower neighbor
        calibrated value
        upper neighbor

    are tested while all other parameters remain fixed.
    """

    results: Dict[str, Dict[str, float]] = {}

    baseline_objective = objective(
        observations,
        calibrated_parameters,
    )

    for parameter in registry:
        values = parameter.values()

        current_value = calibrated_parameters[
            parameter.name
        ]

        lower_candidates = [
            value
            for value in values
            if value < current_value
        ]

        upper_candidates = [
            value
            for value in values
            if value > current_value
        ]

        lower_value = (
            max(lower_candidates)
            if lower_candidates
            else current_value
        )

        upper_value = (
            min(upper_candidates)
            if upper_candidates
            else current_value
        )

        lower_parameters = dict(calibrated_parameters)
        lower_parameters[parameter.name] = lower_value

        upper_parameters = dict(calibrated_parameters)
        upper_parameters[parameter.name] = upper_value

        lower_objective = objective(
            observations,
            lower_parameters,
        )

        upper_objective = objective(
            observations,
            upper_parameters,
        )

        results[parameter.name] = {
            "calibrated_value": current_value,
            "baseline_objective": baseline_objective,
            "lower_value": lower_value,
            "lower_objective": lower_objective,
            "upper_value": upper_value,
            "upper_objective": upper_objective,
            "lower_delta": lower_objective - baseline_objective,
            "upper_delta": upper_objective - baseline_objective,
        }

    return results


# ============================================================================
# COMPLETE CALIBRATION PIPELINE
# ============================================================================

def run_calibration(
    observations: Sequence[Observation],
    train_periods: int,
    registry: Sequence[Parameter],
    passes: int = 3,
    synthetic_demo: bool = False,
) -> CalibrationResult:
    """
    Execute complete Gate 8 calibration.

    The model is calibrated ONLY on training observations.

    Test observations remain unseen until final evaluation.
    """

    train, test = chronological_split(
        observations,
        train_periods,
    )

    engine = CalibrationEngine(registry)

    initial_parameters = engine.default_parameters()

    train_actual = [
        item.observed_score
        for item in train
    ]

    test_actual = [
        item.observed_score
        for item in test
    ]

    train_before_predictions = predict_series(
        train,
        initial_parameters,
    )

    test_before_predictions = predict_series(
        test,
        initial_parameters,
    )

    training_before = calculate_metrics(
        train_actual,
        train_before_predictions,
    )

    test_before = calculate_metrics(
        test_actual,
        test_before_predictions,
    )

    calibrated_parameters = engine.calibrate(
        train,
        passes=passes,
    )

    train_after_predictions = predict_series(
        train,
        calibrated_parameters,
    )

    test_after_predictions = predict_series(
        test,
        calibrated_parameters,
    )

    training_after = calculate_metrics(
        train_actual,
        train_after_predictions,
    )

    test_after = calculate_metrics(
        test_actual,
        test_after_predictions,
    )

    objective_before = objective(
        train,
        initial_parameters,
    )

    objective_after = objective(
        train,
        calibrated_parameters,
    )

    improvement_training_percent = percentage_improvement(
        objective_before,
        objective_after,
    )

    test_objective_before = objective(
        test,
        initial_parameters,
    )

    test_objective_after = objective(
        test,
        calibrated_parameters,
    )

    improvement_test_percent = percentage_improvement(
        test_objective_before,
        test_objective_after,
    )

    sensitivity = parameter_sensitivity(
        train,
        calibrated_parameters,
        registry,
    )

    fingerprint = create_fingerprint(
        observations=observations,
        initial_parameters=initial_parameters,
        calibrated_parameters=calibrated_parameters,
        train_periods=train_periods,
        passes=passes,
    )

    return CalibrationResult(
        initial_parameters=initial_parameters,
        calibrated_parameters=calibrated_parameters,
        training_before=training_before,
        training_after=training_after,
        test_before=test_before,
        test_after=test_after,
        objective_before=objective_before,
        objective_after=objective_after,
        improvement_training_percent=improvement_training_percent,
        improvement_test_percent=improvement_test_percent,
        sensitivity=sensitivity,
        fingerprint=fingerprint,
        synthetic_demo=synthetic_demo,
    )


def percentage_improvement(
    before: float,
    after: float,
) -> float:
    """Calculate percentage reduction in an error objective."""

    if before == 0:
        return 0.0

    return 100.0 * (before - after) / before


# ============================================================================
# FINGERPRINT
# ============================================================================

def create_fingerprint(
    observations: Sequence[Observation],
    initial_parameters: Dict[str, float],
    calibrated_parameters: Dict[str, float],
    train_periods: int,
    passes: int,
) -> str:
    """Create deterministic SHA-256 fingerprint."""

    payload = {
        "observations": [
            asdict(item)
            for item in observations
        ],
        "initial_parameters": initial_parameters,
        "calibrated_parameters": calibrated_parameters,
        "train_periods": train_periods,
        "passes": passes,
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ============================================================================
# EXPORT
# ============================================================================

def result_to_dict(
    result: CalibrationResult,
) -> Dict[str, object]:
    """Convert calibration result into JSON-compatible dictionary."""

    return asdict(result)


def save_json(
    result: CalibrationResult,
    filename: str,
) -> None:
    """Save complete result to JSON."""

    path = Path(filename)

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            result_to_dict(result),
            handle,
            indent=2,
            sort_keys=True,
        )


def save_csv(
    result: CalibrationResult,
    filename: str,
) -> None:
    """
    Save compact calibration summary to CSV.
    """

    rows = [
        {
            "dataset": "training",
            "stage": "before",
            "count": result.training_before.count,
            "mae": result.training_before.mae,
            "rmse": result.training_before.rmse,
            "bias": result.training_before.bias,
            "correlation": result.training_before.correlation,
            "directional_accuracy": (
                result.training_before.directional_accuracy
            ),
            "normalized_rmse": (
                result.training_before.normalized_rmse
            ),
            "validation_score": (
                result.training_before.validation_score
            ),
        },
        {
            "dataset": "training",
            "stage": "after",
            "count": result.training_after.count,
            "mae": result.training_after.mae,
            "rmse": result.training_after.rmse,
            "bias": result.training_after.bias,
            "correlation": result.training_after.correlation,
            "directional_accuracy": (
                result.training_after.directional_accuracy
            ),
            "normalized_rmse": (
                result.training_after.normalized_rmse
            ),
            "validation_score": (
                result.training_after.validation_score
            ),
        },
        {
            "dataset": "holdout_test",
            "stage": "before",
            "count": result.test_before.count,
            "mae": result.test_before.mae,
            "rmse": result.test_before.rmse,
            "bias": result.test_before.bias,
            "correlation": result.test_before.correlation,
            "directional_accuracy": (
                result.test_before.directional_accuracy
            ),
            "normalized_rmse": (
                result.test_before.normalized_rmse
            ),
            "validation_score": (
                result.test_before.validation_score
            ),
        },
        {
            "dataset": "holdout_test",
            "stage": "after",
            "count": result.test_after.count,
            "mae": result.test_after.mae,
            "rmse": result.test_after.rmse,
            "bias": result.test_after.bias,
            "correlation": result.test_after.correlation,
            "directional_accuracy": (
                result.test_after.directional_accuracy
            ),
            "normalized_rmse": (
                result.test_after.normalized_rmse
            ),
            "validation_score": (
                result.test_after.validation_score
            ),
        },
    ]

    path = Path(filename)

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


def save_observations_csv(
    observations: Sequence[Observation],
    filename: str,
) -> None:
    """Export observations so they can be inspected or reused."""

    path = Path(filename)

    fieldnames = [
        "period",
        "economic_signal",
        "climate_risk",
        "food_security",
        "energy_reliability",
        "resilience",
        "governance",
        "observed_score",
        "domain",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for observation in observations:
            writer.writerow(asdict(observation))


# ============================================================================
# REPORTING
# ============================================================================

def format_metrics(
    name: str,
    metrics: Metrics,
) -> str:
    return (
        f"{name}\n"
        f"  count:                {metrics.count}\n"
        f"  MAE:                  {metrics.mae:.4f}\n"
        f"  RMSE:                 {metrics.rmse:.4f}\n"
        f"  bias:                 {metrics.bias:.4f}\n"
        f"  correlation:          {metrics.correlation:.4f}\n"
        f"  directional accuracy: {metrics.directional_accuracy:.4f}\n"
        f"  normalized RMSE:      {metrics.normalized_rmse:.4f}\n"
        f"  validation score:     {metrics.validation_score:.2f}/100\n"
    )


def print_report(
    result: CalibrationResult,
) -> None:
    """Print a human-readable Gate 8 report."""

    print()
    print("=" * 76)
    print("GLOBAL DIGITAL TWIN — GATE 8")
    print("CALIBRATION & PARAMETER ESTIMATION")
    print("=" * 76)

    if result.synthetic_demo:
        print("DATA MODE: SYNTHETIC DEMONSTRATION")
        print(
            "WARNING: Synthetic calibration is not empirical validation."
        )
    else:
        print("DATA MODE: USER-SUPPLIED OBSERVATIONS")

    print()
    print("INITIAL PARAMETERS")
    print("-" * 76)

    for name, value in result.initial_parameters.items():
        print(f"{name:24s}: {value:10.4f}")

    print()
    print("CALIBRATED PARAMETERS")
    print("-" * 76)

    for name, value in result.calibrated_parameters.items():
        initial = result.initial_parameters[name]
        delta = value - initial

        print(
            f"{name:24s}: {value:10.4f}"
            f"  delta={delta:+.4f}"
        )

    print()
    print(format_metrics(
        "TRAINING — BEFORE",
        result.training_before,
    ))

    print(format_metrics(
        "TRAINING — AFTER",
        result.training_after,
    ))

    print(format_metrics(
        "HOLDOUT TEST — BEFORE",
        result.test_before,
    ))

    print(format_metrics(
        "HOLDOUT TEST — AFTER",
        result.test_after,
    ))

    print("OBJECTIVE")
    print("-" * 76)
    print(
        f"Training objective before: "
        f"{result.objective_before:.6f}"
    )
    print(
        f"Training objective after:  "
        f"{result.objective_after:.6f}"
    )

    print()
    print(
        f"Training improvement: "
        f"{result.improvement_training_percent:.2f}%"
    )

    print(
        f"Holdout improvement:  "
        f"{result.improvement_test_percent:.2f}%"
    )

    print()
    print("LOCAL PARAMETER SENSITIVITY")
    print("-" * 76)

    for name, values in result.sensitivity.items():
        print(
            f"{name:24s} "
            f"lower Δ={values['lower_delta']:+.6f} "
            f"upper Δ={values['upper_delta']:+.6f}"
        )

    print()
    print("FINGERPRINT")
    print("-" * 76)
    print(result.fingerprint)

    print()
    print("=" * 76)
    print("GATE 8 COMPLETE")
    print("=" * 76)


# ============================================================================
# SELF TESTS
# ============================================================================

def assert_close(
    left: float,
    right: float,
    tolerance: float = 1e-9,
) -> None:
    if abs(left - right) > tolerance:
        raise AssertionError(
            f"Values are not close: {left} vs {right}"
        )


def self_test() -> bool:
    """
    Run the complete Gate 8 test suite.
    """

    tests = [
        ("parameter registry", test_parameter_registry),
        ("metric calculation", test_metrics),
        ("synthetic data generation", test_synthetic_data),
        ("chronological split", test_chronological_split),
        ("deterministic prediction", test_deterministic_prediction),
        ("calibration improvement", test_calibration_improvement),
        ("holdout evaluation", test_holdout_evaluation),
        ("sensitivity analysis", test_sensitivity),
        ("fingerprint reproducibility", test_fingerprint),
        ("export round trip", test_export),
    ]

    passed = 0
    failed = 0

    print()
    print("GLOBAL DIGITAL TWIN GATE 8 SELF TEST")
    print("=" * 76)

    for name, function in tests:
        try:
            function()
            print(f"PASS: {name}")
            passed += 1
        except Exception as exc:
            print(f"FAIL: {name} -> {exc}")
            failed += 1

    print()
    print("=" * 76)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 76)

    if failed == 0:
        print("GLOBAL DIGITAL TWIN GATE 8: PASS")
        return True

    print("GLOBAL DIGITAL TWIN GATE 8: FAIL")
    return False


def test_parameter_registry() -> None:
    registry = default_parameter_registry()

    assert len(registry) == 7

    names = {
        parameter.name
        for parameter in registry
    }

    expected = {
        "intercept",
        "economic_weight",
        "climate_weight",
        "food_weight",
        "energy_weight",
        "resilience_weight",
        "governance_weight",
    }

    assert names == expected

    for parameter in registry:
        assert parameter.lower <= parameter.default
        assert parameter.default <= parameter.upper
        assert parameter.step > 0
        assert parameter.values()


def test_metrics() -> None:
    actual = [1.0, 2.0, 3.0]
    predicted = [1.0, 2.0, 4.0]

    metrics = calculate_metrics(
        actual,
        predicted,
    )

    assert metrics.count == 3
    assert metrics.mae > 0
    assert metrics.rmse > 0
    assert metrics.correlation > 0


def test_synthetic_data() -> None:
    observations_a, true_a = generate_synthetic_observations(
        periods=40,
        seed=42,
    )

    observations_b, true_b = generate_synthetic_observations(
        periods=40,
        seed=42,
    )

    assert len(observations_a) == 40
    assert len(observations_b) == 40
    assert true_a == true_b
    assert observations_a == observations_b


def test_chronological_split() -> None:
    observations, _ = generate_synthetic_observations(
        periods=20,
        seed=42,
    )

    train, test = chronological_split(
        observations,
        train_periods=14,
    )

    assert len(train) == 14
    assert len(test) == 6

    assert train[-1].period < test[0].period


def test_deterministic_prediction() -> None:
    observations, true_parameters = (
        generate_synthetic_observations(
            periods=20,
            seed=42,
        )
    )

    predictions_a = predict_series(
        observations,
        true_parameters,
    )

    predictions_b = predict_series(
        observations,
        true_parameters,
    )

    assert predictions_a == predictions_b


def test_calibration_improvement() -> None:
    observations, _ = generate_synthetic_observations(
        periods=50,
        seed=42,
    )

    train, _ = chronological_split(
        observations,
        train_periods=35,
    )

    engine = CalibrationEngine(
        default_parameter_registry()
    )

    initial = engine.default_parameters()

    initial_objective = objective(
        train,
        initial,
    )

    calibrated = engine.calibrate(
        train,
        passes=4,
    )

    calibrated_objective = objective(
        train,
        calibrated,
    )

    assert calibrated_objective <= initial_objective + 1e-12


def test_holdout_evaluation() -> None:
    observations, _ = generate_synthetic_observations(
        periods=50,
        seed=42,
    )

    result = run_calibration(
        observations,
        train_periods=35,
        registry=default_parameter_registry(),
        passes=4,
        synthetic_demo=True,
    )

    assert result.training_after.rmse <= (
        result.training_before.rmse + 1e-9
    )

    assert result.test_after.count == 15


def test_sensitivity() -> None:
    observations, _ = generate_synthetic_observations(
        periods=40,
        seed=42,
    )

    train, _ = chronological_split(
        observations,
        train_periods=28,
    )

    registry = default_parameter_registry()

    engine = CalibrationEngine(registry)

    calibrated = engine.calibrate(
        train,
        passes=3,
    )

    sensitivity = parameter_sensitivity(
        train,
        calibrated,
        registry,
    )

    assert len(sensitivity) == len(registry)

    for parameter in registry:
        assert parameter.name in sensitivity


def test_fingerprint() -> None:
    observations_a, _ = generate_synthetic_observations(
        periods=40,
        seed=42,
    )

    observations_b, _ = generate_synthetic_observations(
        periods=40,
        seed=42,
    )

    registry = default_parameter_registry()

    result_a = run_calibration(
        observations_a,
        train_periods=28,
        registry=registry,
        passes=3,
        synthetic_demo=True,
    )

    result_b = run_calibration(
        observations_b,
        train_periods=28,
        registry=registry,
        passes=3,
        synthetic_demo=True,
    )

    assert result_a.fingerprint == result_b.fingerprint


def test_export() -> None:
    """
    Test export using temporary files from the standard library.
    """

    import tempfile

    observations, _ = generate_synthetic_observations(
        periods=30,
        seed=42,
    )

    result = run_calibration(
        observations,
        train_periods=20,
        registry=default_parameter_registry(),
        passes=3,
        synthetic_demo=True,
    )

    with tempfile.TemporaryDirectory() as directory:
        json_file = str(
            Path(directory) / "gate8.json"
        )

        csv_file = str(
            Path(directory) / "gate8.csv"
        )

        observations_file = str(
            Path(directory) / "observations.csv"
        )

        save_json(
            result,
            json_file,
        )

        save_csv(
            result,
            csv_file,
        )

        save_observations_csv(
            observations,
            observations_file,
        )

        assert Path(json_file).exists()
        assert Path(csv_file).exists()
        assert Path(observations_file).exists()

        with Path(json_file).open(
            "r",
            encoding="utf-8",
        ) as handle:
            loaded = json.load(handle)

        assert loaded["fingerprint"] == result.fingerprint


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Gate 8 — "
            "Calibration & Parameter Estimation"
        )
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the Gate 8 self-test suite.",
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=60,
        help="Number of synthetic periods.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Synthetic data random seed.",
    )

    parser.add_argument(
        "--train-periods",
        type=int,
        default=45,
        help="Number of chronological training periods.",
    )

    parser.add_argument(
        "--passes",
        type=int,
        default=4,
        help="Maximum coordinate-search calibration passes.",
    )

    parser.add_argument(
        "--observations",
        type=str,
        default=None,
        help="CSV file containing real observations.",
    )

    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Export calibration results to JSON.",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Export calibration summary to CSV.",
    )

    parser.add_argument(
        "--export-demo",
        type=str,
        default=None,
        help="Export generated demonstration observations to CSV.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return 0 if self_test() else 1

    if args.observations:
        observations = load_observations_csv(
            args.observations
        )

        synthetic_demo = False

    else:
        observations, _ = generate_synthetic_observations(
            periods=args.periods,
            seed=args.seed,
        )

        synthetic_demo = True

        if args.export_demo:
            save_observations_csv(
                observations,
                args.export_demo,
            )

            print(
                f"Demonstration observations exported to "
                f"{args.export_demo}"
            )

    if args.train_periods >= len(observations):
        parser.error(
            "--train-periods must leave at least "
            "two holdout observations."
        )

    result = run_calibration(
        observations=observations,
        train_periods=args.train_periods,
        registry=default_parameter_registry(),
        passes=args.passes,
        synthetic_demo=synthetic_demo,
    )

    print_report(result)

    if args.json:
        save_json(
            result,
            args.json,
        )
        print()
        print(f"JSON written to: {args.json}")

    if args.csv:
        save_csv(
            result,
            args.csv,
        )
        print(f"CSV written to:  {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())