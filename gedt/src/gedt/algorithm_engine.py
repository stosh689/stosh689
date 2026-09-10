"""
GEDT v11 Algorithm Engine

Global Economic Digital Twin
----------------------------

A dependency-free research engine providing:

1. Deterministic economic simulation
2. Pluggable forecasting algorithms
3. Baseline algorithms
4. Error metrics
5. Algorithm comparison and ranking
6. Monte Carlo uncertainty analysis
7. Parameter sensitivity analysis
8. Grid-search optimization
9. Reproducible scenario analysis

This module is intended to provide a transparent computational
foundation for GEDT v11.

IMPORTANT:
This is a research and decision-support framework. It does not
claim to predict the future economy with certainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
import random
from statistics import mean
from typing import Iterable, Sequence


# ============================================================
# CORE ECONOMIC STATE
# ============================================================


@dataclass(frozen=True)
class EconomicState:
    """Economic conditions at one point in time."""

    period: int
    gdp: float
    inflation: float
    unemployment: float


@dataclass(frozen=True)
class Scenario:
    """Economic scenario parameters."""

    name: str = "baseline"
    demand_shock: float = 0.0
    supply_shock: float = 0.0
    policy_rate_change: float = 0.0


@dataclass(frozen=True)
class SimulationResult:
    """Result of a deterministic simulation."""

    scenario: Scenario
    states: tuple[EconomicState, ...]

    @property
    def final_gdp(self) -> float:
        return self.states[-1].gdp

    @property
    def initial_gdp(self) -> float:
        return self.states[0].gdp

    @property
    def gdp_growth(self) -> float:
        if self.initial_gdp == 0:
            return 0.0

        return (
            self.final_gdp / self.initial_gdp
        ) - 1.0

    @property
    def average_inflation(self) -> float:
        return mean(
            state.inflation
            for state in self.states
        )

    @property
    def average_unemployment(self) -> float:
        return mean(
            state.unemployment
            for state in self.states
        )


# ============================================================
# VALIDATION
# ============================================================


def validate_state(state: EconomicState) -> None:
    """Validate an economic state."""

    if state.period < 0:
        raise ValueError(
            "period must be non-negative"
        )

    if state.gdp <= 0:
        raise ValueError(
            "gdp must be positive"
        )

    if not 0 <= state.inflation < 1:
        raise ValueError(
            "inflation must be between 0 and 1"
        )

    if not 0 <= state.unemployment <= 1:
        raise ValueError(
            "unemployment must be between 0 and 1"
        )


def validate_scenario(scenario: Scenario) -> None:
    """Validate scenario parameters."""

    if not scenario.name.strip():
        raise ValueError(
            "scenario name cannot be empty"
        )

    values = (
        scenario.demand_shock,
        scenario.supply_shock,
        scenario.policy_rate_change,
    )

    for value in values:
        if not isinstance(value, (int, float)):
            raise TypeError(
                "scenario parameters must be numeric"
            )


# ============================================================
# DETERMINISTIC ECONOMIC SIMULATOR
# ============================================================


def simulate(
    initial: EconomicState,
    periods: int = 12,
    scenario: Scenario | None = None,
) -> SimulationResult:
    """
    Run the deterministic GEDT economic model.

    The model is intentionally transparent and is intended
    as a baseline research model.
    """

    validate_state(initial)

    if periods < 1:
        raise ValueError(
            "periods must be at least 1"
        )

    scenario = scenario or Scenario()

    validate_scenario(scenario)

    states: list[EconomicState] = [initial]

    current = initial

    for step in range(1, periods + 1):

        growth = (
            0.02
            + 0.04 * scenario.demand_shock
            - 0.03 * scenario.supply_shock
            - 0.01 * scenario.policy_rate_change
        )

        inflation_change = (
            0.0015 * scenario.demand_shock
            + 0.0020 * scenario.supply_shock
            - 0.0010 * scenario.policy_rate_change
        )

        unemployment_change = (
            -0.004 * scenario.demand_shock
            + 0.003 * scenario.supply_shock
            + 0.002 * scenario.policy_rate_change
        )

        next_gdp = current.gdp * exp(growth)

        next_inflation = max(
            0.0,
            min(
                0.99,
                current.inflation
                + inflation_change,
            ),
        )

        next_unemployment = max(
            0.0,
            min(
                1.0,
                current.unemployment
                + unemployment_change,
            ),
        )

        current = EconomicState(
            period=initial.period + step,
            gdp=next_gdp,
            inflation=next_inflation,
            unemployment=next_unemployment,
        )

        states.append(current)

    return SimulationResult(
        scenario=scenario,
        states=tuple(states),
    )


# ============================================================
# ALGORITHM INTERFACE
# ============================================================


class EconomicAlgorithm:
    """
    Base interface for GEDT algorithms.

    Every algorithm should provide:

    - name
    - version
    - fit()
    - predict()
    """

    name = "abstract"
    version = "1.0"

    def fit(
        self,
        data: Sequence[float],
    ) -> "EconomicAlgorithm":
        """Fit the algorithm to historical data."""

        raise NotImplementedError

    def predict(
        self,
        horizon: int = 1,
    ) -> list[float]:
        """Generate predictions."""

        raise NotImplementedError

    def describe(self) -> str:
        """Return algorithm metadata."""

        return (
            f"{self.name} "
            f"v{self.version}"
        )


# ============================================================
# MEAN BASELINE ALGORITHM
# ============================================================


class MeanBaseline(EconomicAlgorithm):
    """
    Simple mean forecasting baseline.

    This is deliberately simple and provides a reference
    against which more sophisticated algorithms can be tested.
    """

    name = "mean_baseline"
    version = "1.0"

    def __init__(self) -> None:
        self._mean = 0.0
        self._fitted = False

    def fit(
        self,
        data: Sequence[float],
    ) -> "MeanBaseline":

        if not data:
            raise ValueError(
                "cannot fit on empty data"
            )

        values = [
            float(value)
            for value in data
        ]

        self._mean = mean(values)
        self._fitted = True

        return self

    def predict(
        self,
        horizon: int = 1,
    ) -> list[float]:

        if not self._fitted:
            raise RuntimeError(
                "algorithm must be fitted before prediction"
            )

        if horizon < 1:
            raise ValueError(
                "horizon must be at least 1"
            )

        return [
            self._mean
            for _ in range(horizon)
        ]


# ============================================================
# LAST-VALUE BASELINE
# ============================================================


class LastValueBaseline(EconomicAlgorithm):
    """
    Persistence model.

    The most recent observation becomes the forecast.
    """

    name = "last_value_baseline"
    version = "1.0"

    def __init__(self) -> None:
        self._last = 0.0
        self._fitted = False

    def fit(
        self,
        data: Sequence[float],
    ) -> "LastValueBaseline":

        if not data:
            raise ValueError(
                "cannot fit on empty data"
            )

        self._last = float(data[-1])
        self._fitted = True

        return self

    def predict(
        self,
        horizon: int = 1,
    ) -> list[float]:

        if not self._fitted:
            raise RuntimeError(
                "algorithm must be fitted before prediction"
            )

        if horizon < 1:
            raise ValueError(
                "horizon must be at least 1"
            )

        return [
            self._last
            for _ in range(horizon)
        ]


# ============================================================
# LINEAR TREND ALGORITHM
# ============================================================


class LinearTrend(EconomicAlgorithm):
    """
    Ordinary least-squares linear trend.

    Implemented without external dependencies so GEDT's
    foundational algorithm layer remains lightweight.
    """

    name = "linear_trend"
    version = "1.0"

    def __init__(self) -> None:
        self._intercept = 0.0
        self._slope = 0.0
        self._fitted = False

    def fit(
        self,
        data: Sequence[float],
    ) -> "LinearTrend":

        if len(data) < 2:
            raise ValueError(
                "linear trend requires at least two observations"
            )

        y = [
            float(value)
            for value in data
        ]

        x = list(range(len(y)))

        x_mean = mean(x)
        y_mean = mean(y)

        numerator = sum(
            (xi - x_mean) * (yi - y_mean)
            for xi, yi in zip(x, y)
        )

        denominator = sum(
            (xi - x_mean) ** 2
            for xi in x
        )

        if denominator == 0:
            raise ValueError(
                "cannot calculate linear trend"
            )

        self._slope = (
            numerator / denominator
        )

        self._intercept = (
            y_mean
            - self._slope * x_mean
        )

        self._fitted = True

        return self

    def predict(
        self,
        horizon: int = 1,
    ) -> list[float]:

        if not self._fitted:
            raise RuntimeError(
                "algorithm must be fitted before prediction"
            )

        if horizon < 1:
            raise ValueError(
                "horizon must be at least 1"
            )

        start = 1

        # The prediction index begins immediately after
        # the fitted sample.
        #
        # The fitted sample length is inferred from the
        # intercept/slope relationship only through stored
        # predictions, so a dedicated counter is maintained
        # below.

        return [
            self._intercept
            + self._slope * (
                self._sample_size + i
            )
            for i in range(horizon)
        ]

    def fit_with_sample_size(
        self,
        data: Sequence[float],
    ) -> "LinearTrend":

        self.fit(data)
        self._sample_size = len(data)

        return self


# ============================================================
# EVALUATION METRICS
# ============================================================


@dataclass(frozen=True)
class Evaluation:
    """Standardized algorithm evaluation."""

    algorithm: str
    samples: int
    mae: float
    mse: float
    rmse: float
    bias: float


def _validate_evaluation_arrays(
    actual: Sequence[float],
    predicted: Sequence[float],
) -> None:

    if not actual:
        raise ValueError(
            "actual data cannot be empty"
        )

    if len(actual) != len(predicted):
        raise ValueError(
            "actual and predicted lengths must match"
        )


def evaluate_predictions(
    actual: Sequence[float],
    predicted: Sequence[float],
    algorithm: str = "unknown",
) -> Evaluation:
    """Calculate standard forecast metrics."""

    _validate_evaluation_arrays(
        actual,
        predicted,
    )

    errors = [
        float(prediction) - float(observed)
        for observed, prediction
        in zip(actual, predicted)
    ]

    absolute_errors = [
        abs(error)
        for error in errors
    ]

    squared_errors = [
        error ** 2
        for error in errors
    ]

    mae = mean(absolute_errors)
    mse = mean(squared_errors)
    rmse = sqrt(mse)
    bias = mean(errors)

    return Evaluation(
        algorithm=algorithm,
        samples=len(actual),
        mae=mae,
        mse=mse,
        rmse=rmse,
        bias=bias,
    )


# ============================================================
# ALGORITHM COMPARISON
# ============================================================


def evaluate_algorithm(
    algorithm: EconomicAlgorithm,
    training_data: Sequence[float],
    actual: Sequence[float],
) -> Evaluation:
    """Fit and evaluate one algorithm."""

    algorithm.fit(training_data)

    predictions = algorithm.predict(
        horizon=len(actual)
    )

    return evaluate_predictions(
        actual,
        predictions,
        algorithm=algorithm.name,
    )


def rank_algorithms(
    algorithms: Iterable[EconomicAlgorithm],
    training_data: Sequence[float],
    actual: Sequence[float],
) -> list[Evaluation]:
    """
    Evaluate and rank algorithms by RMSE.

    Lower RMSE is better.
    """

    evaluations = [
        evaluate_algorithm(
            algorithm,
            training_data,
            actual,
        )
        for algorithm in algorithms
    ]

    return sorted(
        evaluations,
        key=lambda result: result.rmse,
    )


# ============================================================
# MONTE CARLO UNCERTAINTY
# ============================================================


@dataclass(frozen=True)
class MonteCarloSummary:
    """Summary of Monte Carlo simulations."""

    trials: int
    seed: int
    mean_final_gdp: float
    std_final_gdp: float
    minimum_final_gdp: float
    maximum_final_gdp: float
    lower_quantile: float
    upper_quantile: float


def _quantile(
    values: Sequence[float],
    probability: float,
) -> float:

    if not values:
        raise ValueError(
            "values cannot be empty"
        )

    ordered = sorted(values)

    position = (
        probability
        * (len(ordered) - 1)
    )

    lower = int(position)
    upper = min(
        lower + 1,
        len(ordered) - 1,
    )

    weight = position - lower

    return (
        ordered[lower]
        * (1.0 - weight)
        + ordered[upper]
        * weight
    )


def monte_carlo(
    initial: EconomicState,
    scenario: Scenario,
    periods: int = 12,
    trials: int = 1000,
    seed: int = 42,
    shock_std: float = 0.10,
) -> MonteCarloSummary:
    """
    Run a reproducible Monte Carlo scenario analysis.

    Random variation is applied to the scenario shocks.
    """

    if trials < 1:
        raise ValueError(
            "trials must be at least 1"
        )

    if shock_std < 0:
        raise ValueError(
            "shock_std cannot be negative"
        )

    rng = random.Random(seed)

    final_gdp: list[float] = []

    for _ in range(trials):

        randomized = Scenario(
            name=scenario.name,
            demand_shock=(
                scenario.demand_shock
                + rng.gauss(0.0, shock_std)
            ),
            supply_shock=(
                scenario.supply_shock
                + rng.gauss(0.0, shock_std)
            ),
            policy_rate_change=(
                scenario.policy_rate_change
                + rng.gauss(0.0, shock_std)
            ),
        )

        result = simulate(
            initial=initial,
            periods=periods,
            scenario=randomized,
        )

        final_gdp.append(
            result.final_gdp
        )

    average = mean(final_gdp)

    variance = mean(
        (value - average) ** 2
        for value in final_gdp
    )

    standard_deviation = sqrt(variance)

    return MonteCarloSummary(
        trials=trials,
        seed=seed,
        mean_final_gdp=average,
        std_final_gdp=standard_deviation,
        minimum_final_gdp=min(final_gdp),
        maximum_final_gdp=max(final_gdp),
        lower_quantile=_quantile(
            final_gdp,
            0.05,
        ),
        upper_quantile=_quantile(
            final_gdp,
            0.95,
        ),
    )


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================


@dataclass(frozen=True)
class SensitivityResult:
    """Result of a parameter sensitivity experiment."""

    parameter: str
    value: float
    final_gdp: float
    gdp_growth: float


def sensitivity_analysis(
    initial: EconomicState,
    scenario: Scenario,
    parameter: str,
    values: Sequence[float],
    periods: int = 12,
) -> list[SensitivityResult]:
    """
    Evaluate how one scenario parameter changes the result.
    """

    allowed = {
        "demand_shock",
        "supply_shock",
        "policy_rate_change",
    }

    if parameter not in allowed:
        raise ValueError(
            "unsupported sensitivity parameter: "
            + parameter
        )

    results: list[SensitivityResult] = []

    for value in values:

        parameters = {
            "demand_shock":
                scenario.demand_shock,
            "supply_shock":
                scenario.supply_shock,
            "policy_rate_change":
                scenario.policy_rate_change,
        }

        parameters[parameter] = float(value)

        modified = Scenario(
            name=(
                f"{scenario.name}_"
                f"{parameter}_{value}"
            ),
            **parameters,
        )

        simulation = simulate(
            initial,
            periods,
            modified,
        )

        results.append(
            SensitivityResult(
                parameter=parameter,
                value=float(value),
                final_gdp=simulation.final_gdp,
                gdp_growth=simulation.gdp_growth,
            )
        )

    return results


# ============================================================
# GRID-SEARCH OPTIMIZATION
# ============================================================


@dataclass(frozen=True)
class OptimizationResult:
    """Best result from parameter search."""

    parameter: str
    value: float
    objective: float
    final_gdp: float
    gdp_growth: float


def optimize_parameter(
    initial: EconomicState,
    scenario: Scenario,
    parameter: str,
    values: Sequence[float],
    periods: int = 12,
    objective: str = "final_gdp",
) -> OptimizationResult:
    """
    Perform transparent grid-search optimization.

    Default objective maximizes final GDP.

    Supported objectives:

    - final_gdp
    - gdp_growth
    - average_inflation
    - average_unemployment
    """

    sensitivity = sensitivity_analysis(
        initial=initial,
        scenario=scenario,
        parameter=parameter,
        values=values,
        periods=periods,
    )

    candidates = []

    for result in sensitivity:

        modified = Scenario(
            name=scenario.name,
            demand_shock=(
                result.value
                if parameter == "demand_shock"
                else scenario.demand_shock
            ),
            supply_shock=(
                result.value
                if parameter == "supply_shock"
                else scenario.supply_shock
            ),
            policy_rate_change=(
                result.value
                if parameter == "policy_rate_change"
                else scenario.policy_rate_change
            ),
        )

        simulation = simulate(
            initial,
            periods,
            modified,
        )

        if objective == "final_gdp":
            score = simulation.final_gdp

        elif objective == "gdp_growth":
            score = simulation.gdp_growth

        elif objective == "average_inflation":
            score = (
                -simulation.average_inflation
            )

        elif objective == "average_unemployment":
            score = (
                -simulation.average_unemployment
            )

        else:
            raise ValueError(
                "unsupported objective: "
                + objective
            )

        candidates.append(
            (
                score,
                result.value,
                simulation,
            )
        )

    best = max(
        candidates,
        key=lambda item: item[0],
    )

    score, value, simulation = best

    return OptimizationResult(
        parameter=parameter,
        value=value,
        objective=score,
        final_gdp=simulation.final_gdp,
        gdp_growth=simulation.gdp_growth,
    )


# ============================================================
# SCENARIO COMPARISON
# ============================================================


def compare_scenarios(
    initial: EconomicState,
    scenarios: Iterable[Scenario],
    periods: int = 12,
) -> dict[str, SimulationResult]:
    """Run and compare multiple scenarios."""

    results: dict[str, SimulationResult] = {}

    for scenario in scenarios:

        validate_scenario(scenario)

        if scenario.name in results:
            raise ValueError(
                "duplicate scenario name: "
                + scenario.name
            )

        results[scenario.name] = simulate(
            initial=initial,
            periods=periods,
            scenario=scenario,
        )

    return results


# ============================================================
# REPRODUCIBLE BASELINE EXPERIMENT
# ============================================================


def run_baseline_experiment() -> SimulationResult:
    """
    Execute GEDT's canonical baseline experiment.

    This function intentionally uses fixed inputs so that
    future versions can compare results against it.
    """

    initial = EconomicState(
        period=0,
        gdp=100.0,
        inflation=0.02,
        unemployment=0.05,
    )

    baseline = Scenario(
        name="baseline",
        demand_shock=0.0,
        supply_shock=0.0,
        policy_rate_change=0.0,
    )

    return simulate(
        initial=initial,
        periods=12,
        scenario=baseline,
    )


# ============================================================
# ENGINE REPORT
# ============================================================


def engine_report() -> str:
    """Return a human-readable GEDT algorithm report."""

    baseline = run_baseline_experiment()

    return (
        "GEDT v11 ALGORITHM ENGINE\n"
        "=========================\n"
        f"Scenario: "
        f"{baseline.scenario.name}\n"
        f"Periods: "
        f"{len(baseline.states) - 1}\n"
        f"Initial GDP: "
        f"{baseline.initial_gdp:.6f}\n"
        f"Final GDP: "
        f"{baseline.final_gdp:.6f}\n"
        f"GDP Growth: "
        f"{baseline.gdp_growth:.6%}\n"
        f"Average Inflation: "
        f"{baseline.average_inflation:.6%}\n"
        f"Average Unemployment: "
        f"{baseline.average_unemployment:.6%}\n"
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "EconomicState",
    "Scenario",
    "SimulationResult",
    "EconomicAlgorithm",
    "MeanBaseline",
    "LastValueBaseline",
    "LinearTrend",
    "Evaluation",
    "evaluate_predictions",
    "evaluate_algorithm",
    "rank_algorithms",
    "MonteCarloSummary",
    "monte_carlo",
    "SensitivityResult",
    "sensitivity_analysis",
    "OptimizationResult",
    "optimize_parameter",
    "compare_scenarios",
    "run_baseline_experiment",
    "engine_report",
]


# ============================================================
# COMMAND-LINE EXECUTION
# ============================================================


if __name__ == "__main__":

    print(engine_report())

    print("ALGORITHM COMPARISON")
    print("====================")

    training = [
        100.0,
        102.0,
        104.0,
        106.0,
        108.0,
        110.0,
    ]

    actual = [
        112.0,
        114.0,
        116.0,
    ]

    algorithms = [
        MeanBaseline(),
        LastValueBaseline(),
        LinearTrend().fit_with_sample_size(
            training
        ),
    ]

    rankings = rank_algorithms(
        algorithms=algorithms,
        training_data=training,
        actual=actual,
    )

    for position, result in enumerate(
        rankings,
        start=1,
    ):
        print(
            f"{position}. "
            f"{result.algorithm}: "
            f"RMSE={result.rmse:.6f}, "
            f"MAE={result.mae:.6f}, "
            f"Bias={result.bias:.6f}"
        )

    print()
    print("MONTE CARLO")
    print("===========")

    initial = EconomicState(
        period=0,
        gdp=100.0,
        inflation=0.02,
        unemployment=0.05,
    )

    scenario = Scenario(
        name="growth_scenario",
        demand_shock=0.20,
        supply_shock=0.0,
        policy_rate_change=-0.10,
    )

    mc = monte_carlo(
        initial=initial,
        scenario=scenario,
        periods=12,
        trials=1000,
        seed=42,
        shock_std=0.10,
    )

    print(
        f"Trials: {mc.trials}"
    )

    print(
        f"Mean final GDP: "
        f"{mc.mean_final_gdp:.6f}"
    )

    print(
        f"Std final GDP: "
        f"{mc.std_final_gdp:.6f}"
    )

    print(
        f"5%-95% interval: "
        f"{mc.lower_quantile:.6f} - "
        f"{mc.upper_quantile:.6f}"
    )

    print()
    print("SENSITIVITY")
    print("===========")

    sensitivity = sensitivity_analysis(
        initial=initial,
        scenario=scenario,
        parameter="demand_shock",
        values=[
            -0.20,
            -0.10,
            0.00,
            0.10,
            0.20,
            0.30,
        ],
        periods=12,
    )

    for result in sensitivity:
        print(
            f"demand_shock="
            f"{result.value:+.2f} "
            f"final_GDP="
            f"{result.final_gdp:.4f} "
            f"growth="
            f"{result.gdp_growth:.2%}"
        )

    print()
    print("OPTIMIZATION")
    print("============")

    optimization = optimize_parameter(
        initial=initial,
        scenario=scenario,
        parameter="demand_shock",
        values=[
            -0.20,
            -0.10,
            0.00,
            0.10,
            0.20,
            0.30,
        ],
        periods=12,
        objective="final_gdp",
    )

    print(
        f"Best {optimization.parameter}: "
        f"{optimization.value:+.2f}"
    )

    print(
        f"Final GDP: "
        f"{optimization.final_gdp:.6f}"
    )

    print(
        f"GDP Growth: "
        f"{optimization.gdp_growth:.2%}"
    )