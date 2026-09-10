"""
Global Digital Twin - Gate 7
Empirical Validation & Backtesting Engine

Objective
---------
Evaluate whether the Global Digital Twin behaves consistently with
observed historical data.

Gate 7 moves the project from:

    Scenario simulation
        ->
    Optimization
        ->
    Empirical validation

The engine supports:

- observed vs predicted data
- MAE
- RMSE
- bias
- correlation
- directional accuracy
- rolling backtesting
- domain-level validation
- aggregate validation scoring
- synthetic demonstration data
- user-supplied CSV observations
- JSON / CSV export
- deterministic fingerprints
- built-in self-tests

IMPORTANT
---------
The built-in demonstration observations are synthetic.

They are NOT real-world observations and must not be represented
as evidence of model accuracy.

For scientific validation, replace the demonstration dataset with
properly sourced historical observations.
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
from typing import Dict, Iterable, List, Optional, Tuple


# ============================================================================
# VERSION
# ============================================================================

VERSION = "7.0.0"
GATE_NAME = "GLOBAL DIGITAL TWIN GATE 7"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:
    return max(low, min(high, value))


def safe_mean(
    values: Iterable[float],
    default: float = 0.0,
) -> float:

    values = list(values)

    if not values:
        return default

    return statistics.mean(values)


def safe_stdev(
    values: Iterable[float],
    default: float = 0.0,
) -> float:

    values = list(values)

    if len(values) < 2:
        return default

    return statistics.stdev(values)


def fingerprint(data: object) -> str:

    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def mean_absolute_error(
    observed: List[float],
    predicted: List[float],
) -> float:

    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted lengths differ.")

    if not observed:
        return 0.0

    return safe_mean(
        abs(o - p)
        for o, p in zip(observed, predicted)
    )


def root_mean_squared_error(
    observed: List[float],
    predicted: List[float],
) -> float:

    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted lengths differ.")

    if not observed:
        return 0.0

    mse = safe_mean(
        (o - p) ** 2
        for o, p in zip(observed, predicted)
    )

    return math.sqrt(mse)


def mean_bias(
    observed: List[float],
    predicted: List[float],
) -> float:

    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted lengths differ.")

    if not observed:
        return 0.0

    return safe_mean(
        p - o
        for o, p in zip(observed, predicted)
    )


def correlation(
    observed: List[float],
    predicted: List[float],
) -> float:

    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted lengths differ.")

    n = len(observed)

    if n < 2:
        return 0.0

    mean_o = statistics.mean(observed)
    mean_p = statistics.mean(predicted)

    numerator = sum(
        (o - mean_o) * (p - mean_p)
        for o, p in zip(observed, predicted)
    )

    denominator_o = math.sqrt(
        sum((o - mean_o) ** 2 for o in observed)
    )

    denominator_p = math.sqrt(
        sum((p - mean_p) ** 2 for p in predicted)
    )

    denominator = denominator_o * denominator_p

    if denominator == 0.0:
        return 0.0

    return numerator / denominator


def directional_accuracy(
    observed: List[float],
    predicted: List[float],
) -> float:

    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted lengths differ.")

    if len(observed) < 2:
        return 0.0

    correct = 0

    total = 0

    for index in range(1, len(observed)):

        observed_direction = observed[index] - observed[index - 1]
        predicted_direction = predicted[index] - predicted[index - 1]

        observed_sign = (
            1 if observed_direction > 0
            else -1 if observed_direction < 0
            else 0
        )

        predicted_sign = (
            1 if predicted_direction > 0
            else -1 if predicted_direction < 0
            else 0
        )

        if observed_sign == predicted_sign:
            correct += 1

        total += 1

    return correct / total if total else 0.0


def normalized_error(
    rmse: float,
    observed: List[float],
) -> float:

    if not observed:
        return 0.0

    spread = max(observed) - min(observed)

    if spread <= 0.0:
        spread = max(abs(statistics.mean(observed)), 1.0)

    return rmse / spread


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Observation:
    period: int
    domain: str
    metric: str
    observed: float


@dataclass
class Prediction:
    period: int
    domain: str
    metric: str
    predicted: float


@dataclass
class ValidationMetrics:
    domain: str
    metric: str

    observations: int

    mae: float
    rmse: float
    bias: float
    correlation: float
    directional_accuracy: float

    normalized_rmse: float
    validation_score: float

    fingerprint: str


@dataclass
class BacktestResult:
    domain: str
    metric: str

    windows: int
    minimum_training_periods: int

    mean_mae: float
    mean_rmse: float
    mean_bias: float
    mean_correlation: float
    mean_directional_accuracy: float

    validation_score: float

    fingerprint: str


@dataclass
class Gate7Result:
    observations: int
    predictions: int

    domain_results: List[ValidationMetrics]
    backtests: List[BacktestResult]

    overall_mae: float
    overall_rmse: float
    overall_bias: float
    overall_correlation: float
    overall_directional_accuracy: float

    overall_validation_score: float

    status: str

    fingerprint: str


# ============================================================================
# VALIDATION ENGINE
# ============================================================================

class Gate7Validator:

    def __init__(
        self,
        seed: int = 42,
    ):

        self.seed = seed

    # ----------------------------------------------------------------------
    # Metric calculation
    # ----------------------------------------------------------------------

    def validate_series(
        self,
        domain: str,
        metric: str,
        observed: List[float],
        predicted: List[float],
    ) -> ValidationMetrics:

        if len(observed) != len(predicted):
            raise ValueError(
                "Observed and predicted series must have equal length."
            )

        mae = mean_absolute_error(
            observed,
            predicted,
        )

        rmse = root_mean_squared_error(
            observed,
            predicted,
        )

        bias = mean_bias(
            observed,
            predicted,
        )

        corr = correlation(
            observed,
            predicted,
        )

        direction = directional_accuracy(
            observed,
            predicted,
        )

        norm_rmse = normalized_error(
            rmse,
            observed,
        )

        # Convert several diagnostics into a 0-100 validation score.
        error_component = clamp(
            100.0 * (1.0 - min(1.0, norm_rmse))
        )

        correlation_component = (
            clamp((corr + 1.0) * 50.0)
        )

        direction_component = (
            direction * 100.0
        )

        bias_component = clamp(
            100.0 * (
                1.0
                - min(
                    1.0,
                    abs(bias) / max(
                        1.0,
                        statistics.mean(
                            abs(value)
                            for value in observed
                        ),
                    ),
                )
            )
        )

        validation_score = (
            error_component * 0.35
            + correlation_component * 0.25
            + direction_component * 0.25
            + bias_component * 0.15
        )

        return ValidationMetrics(
            domain=domain,
            metric=metric,
            observations=len(observed),
            mae=mae,
            rmse=rmse,
            bias=bias,
            correlation=corr,
            directional_accuracy=direction,
            normalized_rmse=norm_rmse,
            validation_score=validation_score,
            fingerprint=fingerprint({
                "domain": domain,
                "metric": metric,
                "observed": observed,
                "predicted": predicted,
            }),
        )

    # ----------------------------------------------------------------------
    # Dataset validation
    # ----------------------------------------------------------------------

    def validate_dataset(
        self,
        observations: List[Observation],
        predictions: List[Prediction],
    ) -> Gate7Result:

        observation_map = {
            (
                item.period,
                item.domain,
                item.metric,
            ): item.observed
            for item in observations
        }

        prediction_map = {
            (
                item.period,
                item.domain,
                item.metric,
            ): item.predicted
            for item in predictions
        }

        keys = sorted(
            set(observation_map)
            & set(prediction_map)
        )

        grouped: Dict[
            Tuple[str, str],
            List[Tuple[int, float, float]],
        ] = {}

        for period, domain, metric in keys:

            grouped.setdefault(
                (domain, metric),
                [],
            ).append(
                (
                    period,
                    observation_map[
                        (period, domain, metric)
                    ],
                    prediction_map[
                        (period, domain, metric)
                    ],
                )
            )

        domain_results: List[ValidationMetrics] = []

        all_observed: List[float] = []
        all_predicted: List[float] = []

        for (domain, metric), values in sorted(
            grouped.items()
        ):

            values.sort(
                key=lambda item: item[0]
            )

            observed = [
                item[1]
                for item in values
            ]

            predicted = [
                item[2]
                for item in values
            ]

            result = self.validate_series(
                domain=domain,
                metric=metric,
                observed=observed,
                predicted=predicted,
            )

            domain_results.append(result)

            all_observed.extend(observed)
            all_predicted.extend(predicted)

        if all_observed:

            overall_mae = mean_absolute_error(
                all_observed,
                all_predicted,
            )

            overall_rmse = root_mean_squared_error(
                all_observed,
                all_predicted,
            )

            overall_bias = mean_bias(
                all_observed,
                all_predicted,
            )

            overall_corr = correlation(
                all_observed,
                all_predicted,
            )

            overall_direction = directional_accuracy(
                all_observed,
                all_predicted,
            )

        else:

            overall_mae = 0.0
            overall_rmse = 0.0
            overall_bias = 0.0
            overall_corr = 0.0
            overall_direction = 0.0

        if domain_results:

            overall_score = safe_mean(
                item.validation_score
                for item in domain_results
            )

        else:

            overall_score = 0.0

        status = (
            "PASS"
            if overall_score >= 70.0
            else "REVIEW"
        )

        return Gate7Result(
            observations=len(observations),
            predictions=len(predictions),
            domain_results=domain_results,
            backtests=[],
            overall_mae=overall_mae,
            overall_rmse=overall_rmse,
            overall_bias=overall_bias,
            overall_correlation=overall_corr,
            overall_directional_accuracy=overall_direction,
            overall_validation_score=overall_score,
            status=status,
            fingerprint=fingerprint({
                "observations": observations,
                "predictions": predictions,
                "results": domain_results,
            }),
        )

    # ----------------------------------------------------------------------
    # Rolling backtest
    # ----------------------------------------------------------------------

    def rolling_backtest(
        self,
        observations: List[Observation],
        predictions: List[Prediction],
        minimum_training_periods: int = 5,
    ) -> List[BacktestResult]:

        observation_map = {
            (
                item.period,
                item.domain,
                item.metric,
            ): item.observed
            for item in observations
        }

        prediction_map = {
            (
                item.period,
                item.domain,
                item.metric,
            ): item.predicted
            for item in predictions
        }

        grouped: Dict[
            Tuple[str, str],
            List[Tuple[int, float, float]],
        ] = {}

        keys = sorted(
            set(observation_map)
            & set(prediction_map)
        )

        for period, domain, metric in keys:

            grouped.setdefault(
                (domain, metric),
                [],
            ).append(
                (
                    period,
                    observation_map[
                        (period, domain, metric)
                    ],
                    prediction_map[
                        (period, domain, metric)
                    ],
                )
            )

        results: List[BacktestResult] = []

        for (domain, metric), values in sorted(
            grouped.items()
        ):

            values.sort(
                key=lambda item: item[0]
            )

            if len(values) <= minimum_training_periods:
                continue

            window_results: List[ValidationMetrics] = []

            for end in range(
                minimum_training_periods + 1,
                len(values) + 1,
            ):

                test_values = values[
                    minimum_training_periods:end
                ]

                if not test_values:
                    continue

                observed = [
                    item[1]
                    for item in test_values
                ]

                predicted = [
                    item[2]
                    for item in test_values
                ]

                window_results.append(
                    self.validate_series(
                        domain=domain,
                        metric=metric,
                        observed=observed,
                        predicted=predicted,
                    )
                )

            if not window_results:
                continue

            results.append(
                BacktestResult(
                    domain=domain,
                    metric=metric,
                    windows=len(window_results),
                    minimum_training_periods=
                        minimum_training_periods,
                    mean_mae=safe_mean(
                        item.mae
                        for item in window_results
                    ),
                    mean_rmse=safe_mean(
                        item.rmse
                        for item in window_results
                    ),
                    mean_bias=safe_mean(
                        item.bias
                        for item in window_results
                    ),
                    mean_correlation=safe_mean(
                        item.correlation
                        for item in window_results
                    ),
                    mean_directional_accuracy=
                        safe_mean(
                            item.directional_accuracy
                            for item in window_results
                        ),
                    validation_score=safe_mean(
                        item.validation_score
                        for item in window_results
                    ),
                    fingerprint=fingerprint(
                        window_results
                    ),
                )
            )

        return results


# ============================================================================
# DEMONSTRATION DATA
# ============================================================================

def generate_demo_data(
    periods: int = 30,
    seed: int = 42,
) -> Tuple[
    List[Observation],
    List[Prediction],
]:

    """
    Generate synthetic demonstration data.

    These values are intentionally synthetic and must NOT be treated
    as real-world evidence.
    """

    rng = random.Random(seed)

    observations: List[Observation] = []
    predictions: List[Prediction] = []

    domains = {
        "economy": {
            "metric": "growth_index",
            "start": 100.0,
            "trend": 1.1,
            "noise": 1.5,
        },

        "climate": {
            "metric": "risk_index",
            "start": 35.0,
            "trend": 0.35,
            "noise": 1.0,
        },

        "food": {
            "metric": "security_index",
            "start": 72.0,
            "trend": 0.25,
            "noise": 1.2,
        },

        "energy": {
            "metric": "reliability_index",
            "start": 94.0,
            "trend": 0.08,
            "noise": 0.6,
        },

        "resilience": {
            "metric": "resilience_index",
            "start": 60.0,
            "trend": 0.40,
            "noise": 1.0,
        },
    }

    for domain, config in domains.items():

        actual = config["start"]

        for period in range(1, periods + 1):

            actual += (
                config["trend"]
                + rng.gauss(0.0, config["noise"])
            )

            observed = actual

            # Synthetic model prediction with modest systematic error.
            predicted = (
                actual
                + rng.gauss(0.0, config["noise"] * 0.70)
                + config["trend"] * 0.35
            )

            observations.append(
                Observation(
                    period=period,
                    domain=domain,
                    metric=config["metric"],
                    observed=observed,
                )
            )

            predictions.append(
                Prediction(
                    period=period,
                    domain=domain,
                    metric=config["metric"],
                    predicted=predicted,
                )
            )

    return observations, predictions


# ============================================================================
# CSV IMPORT
# ============================================================================

def load_observations_csv(
    path: str,
) -> List[Observation]:

    observations: List[Observation] = []

    with open(
        path,
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(handle)

        required = {
            "period",
            "domain",
            "metric",
            "observed",
        }

        if not required.issubset(
            set(reader.fieldnames or [])
        ):
            raise ValueError(
                "Observation CSV must contain columns: "
                "period, domain, metric, observed"
            )

        for row in reader:

            observations.append(
                Observation(
                    period=int(row["period"]),
                    domain=row["domain"],
                    metric=row["metric"],
                    observed=float(row["observed"]),
                )
            )

    return observations


def load_predictions_csv(
    path: str,
) -> List[Prediction]:

    predictions: List[Prediction] = []

    with open(
        path,
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(handle)

        required = {
            "period",
            "domain",
            "metric",
            "predicted",
        }

        if not required.issubset(
            set(reader.fieldnames or [])
        ):
            raise ValueError(
                "Prediction CSV must contain columns: "
                "period, domain, metric, predicted"
            )

        for row in reader:

            predictions.append(
                Prediction(
                    period=int(row["period"]),
                    domain=row["domain"],
                    metric=row["metric"],
                    predicted=float(row["predicted"]),
                )
            )

    return predictions


# ============================================================================
# CSV EXPORT
# ============================================================================

def save_validation_csv(
    result: Gate7Result,
    path: str,
) -> None:

    rows = []

    for item in result.domain_results:

        rows.append({
            "domain": item.domain,
            "metric": item.metric,
            "observations": item.observations,
            "mae": item.mae,
            "rmse": item.rmse,
            "bias": item.bias,
            "correlation": item.correlation,
            "directional_accuracy":
                item.directional_accuracy,
            "normalized_rmse":
                item.normalized_rmse,
            "validation_score":
                item.validation_score,
        })

    fieldnames = [
        "domain",
        "metric",
        "observations",
        "mae",
        "rmse",
        "bias",
        "correlation",
        "directional_accuracy",
        "normalized_rmse",
        "validation_score",
    ]

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# REPORTING
# ============================================================================

def print_report(
    result: Gate7Result,
) -> None:

    print()
    print("=" * 76)
    print(f"{GATE_NAME} - EMPIRICAL VALIDATION")
    print("=" * 76)

    print(f"Version:                    {VERSION}")
    print(f"Observations:               {result.observations}")
    print(f"Predictions:                {result.predictions}")

    print()
    print("OVERALL VALIDATION")
    print("-" * 76)

    print(f"MAE:                        {result.overall_mae:.4f}")
    print(f"RMSE:                       {result.overall_rmse:.4f}")
    print(f"Bias:                       {result.overall_bias:+.4f}")
    print(
        f"Correlation:                "
        f"{result.overall_correlation:.4f}"
    )

    print(
        f"Directional accuracy:      "
        f"{result.overall_directional_accuracy * 100:.2f}%"
    )

    print(
        f"Validation score:          "
        f"{result.overall_validation_score:.2f}/100"
    )

    print()
    print("DOMAIN RESULTS")
    print("-" * 76)

    header = (
        f"{'Domain':<16}"
        f"{'Metric':<24}"
        f"{'MAE':>9}"
        f"{'RMSE':>9}"
        f"{'Corr':>9}"
        f"{'Dir%':>9}"
        f"{'Score':>9}"
    )

    print(header)
    print("-" * 76)

    for item in result.domain_results:

        print(
            f"{item.domain:<16}"
            f"{item.metric:<24}"
            f"{item.mae:>9.3f}"
            f"{item.rmse:>9.3f}"
            f"{item.correlation:>9.3f}"
            f"{item.directional_accuracy * 100:>8.1f}%"
            f"{item.validation_score:>9.2f}"
        )

    if result.backtests:

        print()
        print("ROLLING BACKTEST")
        print("-" * 76)

        for item in result.backtests:

            print(
                f"{item.domain}/{item.metric}: "
                f"{item.windows} windows | "
                f"RMSE={item.mean_rmse:.3f} | "
                f"Corr={item.mean_correlation:.3f} | "
                f"Direction="
                f"{item.mean_directional_accuracy * 100:.1f}% | "
                f"Score={item.validation_score:.2f}"
            )

    print()
    print(f"STATUS:                     {result.status}")
    print(f"Fingerprint:                {result.fingerprint}")

    print()
    print("=" * 76)

    print(
        "NOTE: Synthetic demonstration data are not evidence of "
        "real-world predictive accuracy."
    )

    print("=" * 76)


# ============================================================================
# SELF TEST
# ============================================================================

def self_test() -> bool:

    print()
    print(f"{GATE_NAME} SELF TEST")
    print("=" * 76)

    passed = 0
    failed = 0

    def check(
        name: str,
        condition: bool,
    ) -> None:

        nonlocal passed, failed

        if condition:
            print(f"PASS: {name}")
            passed += 1
        else:
            print(f"FAIL: {name}")
            failed += 1

    validator = Gate7Validator(
        seed=42
    )

    # Test 1
    check(
        "metric calculation",
        abs(
            mean_absolute_error(
                [1.0, 2.0, 3.0],
                [1.0, 3.0, 2.0],
            )
            - (2.0 / 3.0)
        ) < 1e-9,
    )

    # Test 2
    check(
        "RMSE calculation",
        root_mean_squared_error(
            [1.0, 2.0],
            [1.0, 4.0],
        ) > 0.0,
    )

    # Test 3
    check(
        "correlation calculation",
        correlation(
            [1.0, 2.0, 3.0],
            [2.0, 4.0, 6.0],
        ) > 0.99,
    )

    # Test 4
    check(
        "directional accuracy",
        directional_accuracy(
            [1.0, 2.0, 3.0],
            [2.0, 3.0, 4.0],
        ) == 1.0,
    )

    # Test 5
    observations, predictions = generate_demo_data(
        periods=20,
        seed=42,
    )

    check(
        "demonstration dataset generation",
        len(observations) == 100
        and len(predictions) == 100,
    )

    # Test 6
    result_a = validator.validate_dataset(
        observations,
        predictions,
    )

    check(
        "dataset validation",
        len(result_a.domain_results) == 5,
    )

    # Test 7
    result_b = validator.validate_dataset(
        observations,
        predictions,
    )

    check(
        "deterministic validation",
        result_a.fingerprint == result_b.fingerprint,
    )

    # Test 8
    backtests = validator.rolling_backtest(
        observations,
        predictions,
        minimum_training_periods=5,
    )

    check(
        "rolling backtest",
        len(backtests) == 5,
    )

    print()
    print("=" * 76)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 76)

    if failed == 0:
        print(f"{GATE_NAME}: PASS")
        return True

    print(f"{GATE_NAME}: FAIL")
    return False


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Gate 7 - "
            "Empirical Validation & Backtesting"
        )
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--observations",
        default=None,
        help=(
            "CSV containing period,domain,metric,observed"
        ),
    )

    parser.add_argument(
        "--predictions",
        default=None,
        help=(
            "CSV containing period,domain,metric,predicted"
        ),
    )

    parser.add_argument(
        "--training-periods",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--json",
        dest="json_path",
        default=None,
    )

    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
    )

    return parser


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return 0 if self_test() else 1

    if args.periods <= 0:
        parser.error("--periods must be greater than zero")

    if args.training_periods < 1:
        parser.error(
            "--training-periods must be at least 1"
        )

    validator = Gate7Validator(
        seed=args.seed
    )

    # ----------------------------------------------------------------------
    # Load either real CSV data or synthetic demonstration data.
    # ----------------------------------------------------------------------

    if args.observations or args.predictions:

        if not (
            args.observations
            and args.predictions
        ):
            parser.error(
                "Both --observations and --predictions "
                "must be supplied together."
            )

        observations = load_observations_csv(
            args.observations
        )

        predictions = load_predictions_csv(
            args.predictions
        )

        data_source = "USER-SUPPLIED CSV"

    else:

        observations, predictions = generate_demo_data(
            periods=args.periods,
            seed=args.seed,
        )

        data_source = "SYNTHETIC DEMONSTRATION DATA"

    # ----------------------------------------------------------------------
    # Validate
    # ----------------------------------------------------------------------

    result = validator.validate_dataset(
        observations,
        predictions,
    )

    # ----------------------------------------------------------------------
    # Backtest
    # ----------------------------------------------------------------------

    result.backtests = validator.rolling_backtest(
        observations,
        predictions,
        minimum_training_periods=args.training_periods,
    )

    print_report(result)

    print()
    print(f"Data source: {data_source}")

    # ----------------------------------------------------------------------
    # JSON
    # ----------------------------------------------------------------------

    if args.json_path:

        with open(
            args.json_path,
            "w",
            encoding="utf-8",
        ) as handle:

            json.dump(
                asdict(result),
                handle,
                indent=2,
                sort_keys=True,
            )

        print(
            f"JSON written to: {args.json_path}"
        )

    # ----------------------------------------------------------------------
    # CSV
    # ----------------------------------------------------------------------

    if args.csv_path:

        save_validation_csv(
            result,
            args.csv_path,
        )

        print(
            f"CSV written to: {args.csv_path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())