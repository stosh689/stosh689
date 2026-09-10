"""
Global Digital Twin — Gate 9
Sensitivity & Robustness Engine

Purpose
-------
Gate 9 tests whether conclusions from the Global Digital Twin remain
stable when model parameters, inputs, scenarios, and uncertainty are
perturbed.

Gate 9 provides:

1. Local one-at-a-time parameter sensitivity.
2. Global random parameter sensitivity.
3. Input perturbation analysis.
4. Scenario stress testing.
5. Best-case / worst-case analysis.
6. Monte Carlo robustness analysis.
7. Stability and failure detection.
8. Sensitivity ranking.
9. Robustness scoring.
10. Deterministic fingerprints.
11. JSON / CSV export.
12. Standard-library-only implementation.
13. Automated self-tests.
14. Command-line interface.

IMPORTANT SCIENTIFIC NOTE
-------------------------
This is a research prototype.

A high robustness score does not prove that the model is correct.
Robustness means that conclusions are relatively stable under the
specified perturbations.

Real-world validation still requires properly sourced historical data,
appropriate uncertainty estimates, domain expertise, and independent
validation.

Project direction
-----------------
Gate 1  Domain models
Gate 2  Integration
Gate 3  Common execution
Gate 4  Common data contract
Gate 5  Scenarios + Monte Carlo
Gate 6  Intervention optimization
Gate 7  Empirical validation
Gate 8  Calibration
Gate 9  Sensitivity + robustness
Gate 10 Production / research platform
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass(frozen=True)
class ParameterSpec:
    """Definition of a model parameter and its permitted range."""

    name: str
    default: float
    lower: float
    upper: float
    description: str


@dataclass(frozen=True)
class ScenarioSpec:
    """Definition of a scenario-level perturbation."""

    name: str
    economic_delta: float
    climate_delta: float
    food_delta: float
    energy_delta: float
    resilience_delta: float
    governance_delta: float


@dataclass(frozen=True)
class InputState:
    """Normalized input state for the digital twin."""

    economic_signal: float
    climate_risk: float
    food_security: float
    energy_reliability: float
    resilience: float
    governance: float


@dataclass
class Evaluation:
    """Result of one model evaluation."""

    score: float
    economic_component: float
    climate_component: float
    food_component: float
    energy_component: float
    resilience_component: float
    governance_component: float


@dataclass
class SensitivityRecord:
    """Sensitivity result for one parameter or input."""

    name: str
    baseline_score: float
    low_score: float
    high_score: float
    low_delta: float
    high_delta: float
    absolute_effect: float
    normalized_sensitivity: float


@dataclass
class ScenarioResult:
    """Result from a scenario stress test."""

    scenario: str
    score: float
    delta_from_baseline: float
    resilience_ratio: float
    status: str


@dataclass
class MonteCarloSummary:
    """Summary of robustness Monte Carlo simulation."""

    runs: int
    mean: float
    median: float
    minimum: float
    maximum: float
    p05: float
    p25: float
    p75: float
    p95: float
    standard_deviation: float
    probability_below_40: float
    probability_below_50: float
    probability_above_70: float
    probability_above_80: float
    range_width: float
    coefficient_of_variation: float


@dataclass
class Gate9Result:
    """Complete Gate 9 result."""

    baseline_score: float
    local_parameter_sensitivity: List[SensitivityRecord]
    input_sensitivity: List[SensitivityRecord]
    scenario_results: List[ScenarioResult]
    monte_carlo: MonteCarloSummary

    best_case_score: float
    worst_case_score: float

    parameter_robustness_score: float
    input_robustness_score: float
    scenario_robustness_score: float
    monte_carlo_robustness_score: float
    overall_robustness_score: float

    failure_flags: List[str]
    warning_flags: List[str]

    fingerprint: str


# ============================================================================
# PARAMETER REGISTRY
# ============================================================================

def default_parameter_registry() -> List[ParameterSpec]:
    """
    Gate 9 parameter registry.

    These parameters are compatible with the Gate 8 conceptual model.
    """

    return [
        ParameterSpec(
            name="intercept",
            default=52.0,
            lower=40.0,
            upper=60.0,
            description="Baseline global score.",
        ),
        ParameterSpec(
            name="economic_weight",
            default=9.0,
            lower=4.0,
            upper=14.0,
            description="Economic contribution.",
        ),
        ParameterSpec(
            name="climate_weight",
            default=11.0,
            lower=5.0,
            upper=17.0,
            description="Climate-risk penalty.",
        ),
        ParameterSpec(
            name="food_weight",
            default=7.0,
            lower=3.0,
            upper=13.0,
            description="Food-security contribution.",
        ),
        ParameterSpec(
            name="energy_weight",
            default=8.0,
            lower=3.0,
            upper=13.0,
            description="Energy-reliability contribution.",
        ),
        ParameterSpec(
            name="resilience_weight",
            default=10.0,
            lower=4.0,
            upper=16.0,
            description="Resilience contribution.",
        ),
        ParameterSpec(
            name="governance_weight",
            default=6.0,
            lower=2.0,
            upper=12.0,
            description="Governance contribution.",
        ),
    ]


def default_scenarios() -> List[ScenarioSpec]:
    """Return controlled stress scenarios."""

    return [
        ScenarioSpec(
            name="baseline",
            economic_delta=0.00,
            climate_delta=0.00,
            food_delta=0.00,
            energy_delta=0.00,
            resilience_delta=0.00,
            governance_delta=0.00,
        ),
        ScenarioSpec(
            name="mild_stress",
            economic_delta=-0.05,
            climate_delta=0.05,
            food_delta=-0.05,
            energy_delta=-0.05,
            resilience_delta=-0.03,
            governance_delta=-0.03,
        ),
        ScenarioSpec(
            name="climate_stress",
            economic_delta=-0.03,
            climate_delta=0.15,
            food_delta=-0.08,
            energy_delta=-0.05,
            resilience_delta=-0.05,
            governance_delta=0.00,
        ),
        ScenarioSpec(
            name="food_stress",
            economic_delta=-0.02,
            climate_delta=0.05,
            food_delta=-0.15,
            energy_delta=-0.03,
            resilience_delta=-0.05,
            governance_delta=0.00,
        ),
        ScenarioSpec(
            name="energy_crisis",
            economic_delta=-0.06,
            climate_delta=0.04,
            food_delta=-0.04,
            energy_delta=-0.18,
            resilience_delta=-0.06,
            governance_delta=-0.02,
        ),
        ScenarioSpec(
            name="governance_stress",
            economic_delta=-0.04,
            climate_delta=0.04,
            food_delta=-0.04,
            energy_delta=-0.04,
            resilience_delta=-0.05,
            governance_delta=-0.15,
        ),
        ScenarioSpec(
            name="compound_crisis",
            economic_delta=-0.12,
            climate_delta=0.15,
            food_delta=-0.12,
            energy_delta=-0.12,
            resilience_delta=-0.12,
            governance_delta=-0.08,
        ),
        ScenarioSpec(
            name="resilience_first",
            economic_delta=0.03,
            climate_delta=-0.05,
            food_delta=0.07,
            energy_delta=0.06,
            resilience_delta=0.12,
            governance_delta=0.06,
        ),
        ScenarioSpec(
            name="best_case",
            economic_delta=0.08,
            climate_delta=-0.10,
            food_delta=0.10,
            energy_delta=0.10,
            resilience_delta=0.12,
            governance_delta=0.08,
        ),
    ]


# ============================================================================
# MODEL
# ============================================================================

def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """Bound normalized model inputs."""

    return min(upper, max(lower, value))


def evaluate(
    state: InputState,
    parameters: Dict[str, float],
) -> Evaluation:
    """
    Evaluate the conceptual global score model.

    Climate risk is a negative factor.
    All other normalized factors are positive contributions.
    """

    economic_component = (
        parameters["economic_weight"]
        * state.economic_signal
    )

    climate_component = (
        parameters["climate_weight"]
        * state.climate_risk
    )

    food_component = (
        parameters["food_weight"]
        * state.food_security
    )

    energy_component = (
        parameters["energy_weight"]
        * state.energy_reliability
    )

    resilience_component = (
        parameters["resilience_weight"]
        * state.resilience
    )

    governance_component = (
        parameters["governance_weight"]
        * state.governance
    )

    raw_score = (
        parameters["intercept"]
        + economic_component
        - climate_component
        + food_component
        + energy_component
        + resilience_component
        + governance_component
    )

    score = min(100.0, max(0.0, raw_score))

    return Evaluation(
        score=score,
        economic_component=economic_component,
        climate_component=-climate_component,
        food_component=food_component,
        energy_component=energy_component,
        resilience_component=resilience_component,
        governance_component=governance_component,
    )


def default_input_state() -> InputState:
    """Default normalized global state."""

    return InputState(
        economic_signal=0.65,
        climate_risk=0.35,
        food_security=0.70,
        energy_reliability=0.72,
        resilience=0.68,
        governance=0.65,
    )


def apply_scenario(
    state: InputState,
    scenario: ScenarioSpec,
) -> InputState:
    """Apply a scenario perturbation while preserving input bounds."""

    return InputState(
        economic_signal=clamp(
            state.economic_signal + scenario.economic_delta
        ),
        climate_risk=clamp(
            state.climate_risk + scenario.climate_delta
        ),
        food_security=clamp(
            state.food_security + scenario.food_delta
        ),
        energy_reliability=clamp(
            state.energy_reliability + scenario.energy_delta
        ),
        resilience=clamp(
            state.resilience + scenario.resilience_delta
        ),
        governance=clamp(
            state.governance + scenario.governance_delta
        ),
    )


# ============================================================================
# PARAMETER UTILITIES
# ============================================================================

def default_parameters(
    registry: Sequence[ParameterSpec],
) -> Dict[str, float]:
    return {
        item.name: item.default
        for item in registry
    }


def validate_parameters(
    parameters: Dict[str, float],
    registry: Sequence[ParameterSpec],
) -> None:
    """Verify that every parameter exists and is bounded."""

    expected = {
        item.name
        for item in registry
    }

    if set(parameters) != expected:
        raise ValueError("Parameter set does not match registry.")

    for item in registry:
        value = parameters[item.name]

        if not math.isfinite(value):
            raise ValueError(
                f"Non-finite parameter: {item.name}"
            )

        if value < item.lower or value > item.upper:
            raise ValueError(
                f"Parameter out of bounds: {item.name}"
            )


# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================

def make_sensitivity_record(
    name: str,
    baseline_score: float,
    low_score: float,
    high_score: float,
    perturbation_size: float,
) -> SensitivityRecord:
    """Create a standardized sensitivity record."""

    low_delta = low_score - baseline_score
    high_delta = high_score - baseline_score

    absolute_effect = max(
        abs(low_delta),
        abs(high_delta),
    )

    normalized_sensitivity = (
        absolute_effect / perturbation_size
        if perturbation_size > 0
        else 0.0
    )

    return SensitivityRecord(
        name=name,
        baseline_score=baseline_score,
        low_score=low_score,
        high_score=high_score,
        low_delta=low_delta,
        high_delta=high_delta,
        absolute_effect=absolute_effect,
        normalized_sensitivity=normalized_sensitivity,
    )


def local_parameter_sensitivity(
    state: InputState,
    parameters: Dict[str, float],
    registry: Sequence[ParameterSpec],
    fraction: float = 0.10,
) -> List[SensitivityRecord]:
    """
    Perturb each parameter approximately ±10%.

    Bounds are always respected.
    """

    baseline = evaluate(
        state,
        parameters,
    ).score

    records: List[SensitivityRecord] = []

    for spec in registry:
        current = parameters[spec.name]

        low = max(
            spec.lower,
            current * (1.0 - fraction),
        )

        high = min(
            spec.upper,
            current * (1.0 + fraction),
        )

        if high == low:
            continue

        low_parameters = dict(parameters)
        high_parameters = dict(parameters)

        low_parameters[spec.name] = low
        high_parameters[spec.name] = high

        low_score = evaluate(
            state,
            low_parameters,
        ).score

        high_score = evaluate(
            state,
            high_parameters,
        ).score

        records.append(
            make_sensitivity_record(
                name=spec.name,
                baseline_score=baseline,
                low_score=low_score,
                high_score=high_score,
                perturbation_size=max(
                    abs(high - low),
                    1e-12,
                ),
            )
        )

    records.sort(
        key=lambda item: item.absolute_effect,
        reverse=True,
    )

    return records


def input_sensitivity(
    state: InputState,
    parameters: Dict[str, float],
    fraction: float = 0.10,
) -> List[SensitivityRecord]:
    """Perturb each normalized input by approximately ±10%."""

    baseline = evaluate(
        state,
        parameters,
    ).score

    fields = [
        "economic_signal",
        "climate_risk",
        "food_security",
        "energy_reliability",
        "resilience",
        "governance",
    ]

    records: List[SensitivityRecord] = []

    for field_name in fields:
        current = getattr(
            state,
            field_name,
        )

        low = clamp(
            current - fraction
        )

        high = clamp(
            current + fraction
        )

        low_values = {
            field: getattr(state, field)
            for field in fields
        }

        high_values = dict(low_values)

        low_values[field_name] = low
        high_values[field_name] = high

        low_state = InputState(**low_values)
        high_state = InputState(**high_values)

        low_score = evaluate(
            low_state,
            parameters,
        ).score

        high_score = evaluate(
            high_state,
            parameters,
        ).score

        records.append(
            make_sensitivity_record(
                name=field_name,
                baseline_score=baseline,
                low_score=low_score,
                high_score=high_score,
                perturbation_size=max(
                    abs(high - low),
                    1e-12,
                ),
            )
        )

    records.sort(
        key=lambda item: item.absolute_effect,
        reverse=True,
    )

    return records


# ============================================================================
# SCENARIO STRESS TESTING
# ============================================================================

def scenario_analysis(
    state: InputState,
    parameters: Dict[str, float],
    scenarios: Sequence[ScenarioSpec],
) -> List[ScenarioResult]:
    """Evaluate every registered scenario."""

    baseline = evaluate(
        state,
        parameters,
    ).score

    results: List[ScenarioResult] = []

    for scenario in scenarios:
        scenario_state = apply_scenario(
            state,
            scenario,
        )

        score = evaluate(
            scenario_state,
            parameters,
        ).score

        delta = score - baseline

        if baseline == 0:
            resilience_ratio = 0.0
        else:
            resilience_ratio = score / baseline

        if score < 40:
            status = "critical"
        elif score < 50:
            status = "high_risk"
        elif score < 60:
            status = "watch"
        else:
            status = "stable"

        results.append(
            ScenarioResult(
                scenario=scenario.name,
                score=score,
                delta_from_baseline=delta,
                resilience_ratio=resilience_ratio,
                status=status,
            )
        )

    return results


# ============================================================================
# MONTE CARLO ROBUSTNESS
# ============================================================================

def percentile(
    values: Sequence[float],
    percentage: float,
) -> float:
    """Linear-interpolated percentile."""

    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (
        percentage / 100.0
        * (len(ordered) - 1)
    )

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    weight = position - lower

    return (
        ordered[lower] * (1.0 - weight)
        + ordered[upper] * weight
    )


def monte_carlo_robustness(
    state: InputState,
    parameters: Dict[str, float],
    registry: Sequence[ParameterSpec],
    runs: int = 1000,
    seed: int = 42,
    parameter_uncertainty: float = 0.10,
    input_uncertainty: float = 0.05,
) -> MonteCarloSummary:
    """
    Randomly perturb both parameters and inputs.

    The random generator is locally seeded for reproducibility.
    """

    if runs < 10:
        raise ValueError("At least 10 Monte Carlo runs are required.")

    rng = random.Random(seed)

    scores: List[float] = []

    for _ in range(runs):
        perturbed_parameters = {}

        for spec in registry:
            center = parameters[spec.name]

            half_range = (
                spec.upper - spec.lower
            ) * parameter_uncertainty

            value = rng.uniform(
                center - half_range,
                center + half_range,
            )

            value = min(
                spec.upper,
                max(spec.lower, value),
            )

            perturbed_parameters[spec.name] = value

        values = {
            "economic_signal": state.economic_signal,
            "climate_risk": state.climate_risk,
            "food_security": state.food_security,
            "energy_reliability": state.energy_reliability,
            "resilience": state.resilience,
            "governance": state.governance,
        }

        for field in values:
            values[field] = clamp(
                values[field]
                + rng.uniform(
                    -input_uncertainty,
                    input_uncertainty,
                )
            )

        perturbed_state = InputState(**values)

        score = evaluate(
            perturbed_state,
            perturbed_parameters,
        ).score

        scores.append(score)

    mean = statistics.mean(scores)
    median = statistics.median(scores)

    standard_deviation = (
        statistics.stdev(scores)
        if len(scores) > 1
        else 0.0
    )

    if mean == 0:
        coefficient_of_variation = 0.0
    else:
        coefficient_of_variation = (
            standard_deviation / abs(mean)
        )

    return MonteCarloSummary(
        runs=runs,
        mean=mean,
        median=median,
        minimum=min(scores),
        maximum=max(scores),
        p05=percentile(scores, 5),
        p25=percentile(scores, 25),
        p75=percentile(scores, 75),
        p95=percentile(scores, 95),
        standard_deviation=standard_deviation,
        probability_below_40=(
            sum(score < 40 for score in scores)
            / runs
        ),
        probability_below_50=(
            sum(score < 50 for score in scores)
            / runs
        ),
        probability_above_70=(
            sum(score > 70 for score in scores)
            / runs
        ),
        probability_above_80=(
            sum(score > 80 for score in scores)
            / runs
        ),
        range_width=max(scores) - min(scores),
        coefficient_of_variation=coefficient_of_variation,
    )


# ============================================================================
# ROBUSTNESS SCORING
# ============================================================================

def parameter_robustness(
    records: Sequence[SensitivityRecord],
) -> float:
    """
    Convert parameter sensitivity into a bounded robustness score.

    Lower sensitivity means higher robustness.

    The score is intentionally heuristic and should not be interpreted
    as a universal scientific standard.
    """

    if not records:
        return 0.0

    average_effect = statistics.mean(
        record.absolute_effect
        for record in records
    )

    score = 100.0 / (
        1.0 + average_effect
    )

    return min(100.0, max(0.0, score))


def input_robustness(
    records: Sequence[SensitivityRecord],
) -> float:
    """Calculate robustness from input sensitivity."""

    if not records:
        return 0.0

    average_effect = statistics.mean(
        record.absolute_effect
        for record in records
    )

    score = 100.0 / (
        1.0 + average_effect
    )

    return min(100.0, max(0.0, score))


def scenario_robustness(
    baseline_score: float,
    results: Sequence[ScenarioResult],
) -> float:
    """
    Score scenario stability.

    Large downside movements reduce the score.
    """

    if not results or baseline_score <= 0:
        return 0.0

    stress_results = [
        result
        for result in results
        if result.scenario != "baseline"
        and result.scenario != "best_case"
    ]

    if not stress_results:
        return 100.0

    worst_score = min(
        result.score
        for result in stress_results
    )

    relative_loss = max(
        0.0,
        (baseline_score - worst_score)
        / baseline_score,
    )

    score = 100.0 * (
        1.0 - min(1.0, relative_loss)
    )

    return score


def monte_carlo_robustness_score(
    summary: MonteCarloSummary,
) -> float:
    """
    Score Monte Carlo stability.

    Penalizes:
    - high coefficient of variation
    - large lower-tail probability
    """

    variability_penalty = min(
        1.0,
        summary.coefficient_of_variation * 5.0,
    )

    downside_penalty = min(
        1.0,
        summary.probability_below_50,
    )

    score = 100.0 * (
        1.0
        - 0.55 * variability_penalty
        - 0.45 * downside_penalty
    )

    return min(100.0, max(0.0, score))


# ============================================================================
# FAILURE / WARNING DETECTION
# ============================================================================

def detect_flags(
    baseline_score: float,
    parameter_records: Sequence[SensitivityRecord],
    input_records: Sequence[SensitivityRecord],
    scenario_results: Sequence[ScenarioResult],
    monte_carlo: MonteCarloSummary,
) -> Tuple[List[str], List[str]]:
    """Identify structural stress indicators."""

    failures: List[str] = []
    warnings: List[str] = []

    if not math.isfinite(baseline_score):
        failures.append(
            "Baseline score is not finite."
        )

    if baseline_score < 0 or baseline_score > 100:
        failures.append(
            "Baseline score escaped the expected 0–100 range."
        )

    if not parameter_records:
        failures.append(
            "Parameter sensitivity produced no records."
        )

    if not input_records:
        failures.append(
            "Input sensitivity produced no records."
        )

    if not scenario_results:
        failures.append(
            "Scenario analysis produced no results."
        )

    critical_scenarios = [
        item
        for item in scenario_results
        if item.status == "critical"
    ]

    high_risk_scenarios = [
        item
        for item in scenario_results
        if item.status == "high_risk"
    ]

    if critical_scenarios:
        warnings.append(
            f"{len(critical_scenarios)} scenario(s) produced "
            "critical scores."
        )

    if high_risk_scenarios:
        warnings.append(
            f"{len(high_risk_scenarios)} scenario(s) produced "
            "high-risk scores."
        )

    if monte_carlo.probability_below_40 > 0.25:
        warnings.append(
            "Monte Carlo probability below 40 exceeds 25%."
        )

    if monte_carlo.coefficient_of_variation > 0.10:
        warnings.append(
            "Monte Carlo coefficient of variation exceeds 10%."
        )

    if monte_carlo.range_width > 30:
        warnings.append(
            "Monte Carlo score range exceeds 30 points."
        )

    if any(
        record.absolute_effect > 10
        for record in parameter_records
    ):
        warnings.append(
            "At least one parameter has a >10-point local effect."
        )

    if any(
        record.absolute_effect > 10
        for record in input_records
    ):
        warnings.append(
            "At least one input has a >10-point local effect."
        )

    return failures, warnings


# ============================================================================
# FINGERPRINT
# ============================================================================

def create_fingerprint(
    result_without_fingerprint: Dict[str, object],
) -> str:
    """Generate deterministic SHA-256 result fingerprint."""

    canonical = json.dumps(
        result_without_fingerprint,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ============================================================================
# COMPLETE GATE 9 PIPELINE
# ============================================================================

def run_gate9(
    state: InputState | None = None,
    parameters: Dict[str, float] | None = None,
    registry: Sequence[ParameterSpec] | None = None,
    scenarios: Sequence[ScenarioSpec] | None = None,
    runs: int = 1000,
    seed: int = 42,
) -> Gate9Result:
    """Execute the complete Gate 9 robustness pipeline."""

    if state is None:
        state = default_input_state()

    if registry is None:
        registry = default_parameter_registry()

    if parameters is None:
        parameters = default_parameters(registry)

    if scenarios is None:
        scenarios = default_scenarios()

    validate_parameters(
        parameters,
        registry,
    )

    baseline_score = evaluate(
        state,
        parameters,
    ).score

    parameter_records = local_parameter_sensitivity(
        state,
        parameters,
        registry,
    )

    input_records = input_sensitivity(
        state,
        parameters,
    )

    scenario_results = scenario_analysis(
        state,
        parameters,
        scenarios,
    )

    monte_carlo = monte_carlo_robustness(
        state=state,
        parameters=parameters,
        registry=registry,
        runs=runs,
        seed=seed,
    )

    best_case_score = max(
        item.score
        for item in scenario_results
    )

    worst_case_score = min(
        item.score
        for item in scenario_results
    )

    parameter_score = parameter_robustness(
        parameter_records
    )

    input_score = input_robustness(
        input_records
    )

    scenario_score = scenario_robustness(
        baseline_score,
        scenario_results,
    )

    monte_carlo_score = monte_carlo_robustness_score(
        monte_carlo
    )

    overall_score = (
        0.25 * parameter_score
        + 0.20 * input_score
        + 0.30 * scenario_score
        + 0.25 * monte_carlo_score
    )

    failures, warnings = detect_flags(
        baseline_score=baseline_score,
        parameter_records=parameter_records,
        input_records=input_records,
        scenario_results=scenario_results,
        monte_carlo=monte_carlo,
    )

    result_data = {
        "baseline_score": baseline_score,
        "local_parameter_sensitivity": [
            asdict(item)
            for item in parameter_records
        ],
        "input_sensitivity": [
            asdict(item)
            for item in input_records
        ],
        "scenario_results": [
            asdict(item)
            for item in scenario_results
        ],
        "monte_carlo": asdict(monte_carlo),
        "best_case_score": best_case_score,
        "worst_case_score": worst_case_score,
        "parameter_robustness_score": parameter_score,
        "input_robustness_score": input_score,
        "scenario_robustness_score": scenario_score,
        "monte_carlo_robustness_score": monte_carlo_score,
        "overall_robustness_score": overall_score,
        "failure_flags": failures,
        "warning_flags": warnings,
        "state": asdict(state),
        "parameters": parameters,
        "seed": seed,
    }

    fingerprint = create_fingerprint(
        result_data
    )

    return Gate9Result(
        baseline_score=baseline_score,
        local_parameter_sensitivity=parameter_records,
        input_sensitivity=input_records,
        scenario_results=scenario_results,
        monte_carlo=monte_carlo,
        best_case_score=best_case_score,
        worst_case_score=worst_case_score,
        parameter_robustness_score=parameter_score,
        input_robustness_score=input_score,
        scenario_robustness_score=scenario_score,
        monte_carlo_robustness_score=monte_carlo_score,
        overall_robustness_score=overall_score,
        failure_flags=failures,
        warning_flags=warnings,
        fingerprint=fingerprint,
    )


# ============================================================================
# REPORTING
# ============================================================================

def robustness_label(score: float) -> str:
    """Convert robustness score into a qualitative research label."""

    if score >= 80:
        return "strong"
    if score >= 65:
        return "moderate"
    if score >= 50:
        return "mixed"
    return "weak"


def print_report(
    result: Gate9Result,
) -> None:
    """Print complete Gate 9 report."""

    print()
    print("=" * 78)
    print("GLOBAL DIGITAL TWIN — GATE 9")
    print("SENSITIVITY & ROBUSTNESS ENGINE")
    print("=" * 78)

    print()
    print("BASELINE")
    print("-" * 78)
    print(
        f"Baseline score:     {result.baseline_score:.4f}"
    )
    print(
        f"Best scenario:      {result.best_case_score:.4f}"
    )
    print(
        f"Worst scenario:     {result.worst_case_score:.4f}"
    )

    print()
    print("PARAMETER SENSITIVITY")
    print("-" * 78)

    for record in result.local_parameter_sensitivity:
        print(
            f"{record.name:24s}"
            f" low={record.low_delta:+8.3f}"
            f" high={record.high_delta:+8.3f}"
            f" effect={record.absolute_effect:8.3f}"
        )

    print()
    print("INPUT SENSITIVITY")
    print("-" * 78)

    for record in result.input_sensitivity:
        print(
            f"{record.name:24s}"
            f" low={record.low_delta:+8.3f}"
            f" high={record.high_delta:+8.3f}"
            f" effect={record.absolute_effect:8.3f}"
        )

    print()
    print("SCENARIO STRESS TEST")
    print("-" * 78)

    for scenario in result.scenario_results:
        print(
            f"{scenario.scenario:24s}"
            f" score={scenario.score:8.3f}"
            f" delta={scenario.delta_from_baseline:+8.3f}"
            f" status={scenario.status}"
        )

    print()
    print("MONTE CARLO ROBUSTNESS")
    print("-" * 78)

    mc = result.monte_carlo

    print(f"runs:                   {mc.runs}")
    print(f"mean:                   {mc.mean:.4f}")
    print(f"median:                 {mc.median:.4f}")
    print(f"minimum:                {mc.minimum:.4f}")
    print(f"maximum:                {mc.maximum:.4f}")
    print(f"p05:                    {mc.p05:.4f}")
    print(f"p25:                    {mc.p25:.4f}")
    print(f"p75:                    {mc.p75:.4f}")
    print(f"p95:                    {mc.p95:.4f}")
    print(f"standard deviation:     {mc.standard_deviation:.4f}")
    print(
        f"probability < 40:      "
        f"{mc.probability_below_40:.4f}"
    )
    print(
        f"probability < 50:      "
        f"{mc.probability_below_50:.4f}"
    )
    print(
        f"probability > 70:      "
        f"{mc.probability_above_70:.4f}"
    )
    print(
        f"probability > 80:      "
        f"{mc.probability_above_80:.4f}"
    )
    print(
        f"range width:            "
        f"{mc.range_width:.4f}"
    )
    print(
        f"coefficient variation: "
        f"{mc.coefficient_of_variation:.4f}"
    )

    print()
    print("ROBUSTNESS SCORES")
    print("-" * 78)

    print(
        f"Parameter robustness:  "
        f"{result.parameter_robustness_score:.2f}/100"
    )

    print(
        f"Input robustness:      "
        f"{result.input_robustness_score:.2f}/100"
    )

    print(
        f"Scenario robustness:   "
        f"{result.scenario_robustness_score:.2f}/100"
    )

    print(
        f"Monte Carlo robustness:"
        f" {result.monte_carlo_robustness_score:.2f}/100"
    )

    print(
        f"OVERALL ROBUSTNESS:    "
        f"{result.overall_robustness_score:.2f}/100"
        f" ({robustness_label(result.overall_robustness_score)})"
    )

    print()
    print("FAILURE FLAGS")
    print("-" * 78)

    if result.failure_flags:
        for flag in result.failure_flags:
            print(f"FAILURE: {flag}")
    else:
        print("None")

    print()
    print("WARNING FLAGS")
    print("-" * 78)

    if result.warning_flags:
        for flag in result.warning_flags:
            print(f"WARNING: {flag}")
    else:
        print("None")

    print()
    print("FINGERPRINT")
    print("-" * 78)
    print(result.fingerprint)

    print()
    print("=" * 78)
    print("GLOBAL DIGITAL TWIN GATE 9 COMPLETE")
    print("=" * 78)


# ============================================================================
# EXPORT
# ============================================================================

def result_to_dict(
    result: Gate9Result,
) -> Dict[str, object]:
    return asdict(result)


def save_json(
    result: Gate9Result,
    filename: str,
) -> None:
    """Export complete Gate 9 result."""

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
    result: Gate9Result,
    filename: str,
) -> None:
    """Export a flat summary suitable for spreadsheets."""

    rows = [
        {
            "section": "baseline",
            "name": "baseline_score",
            "value": result.baseline_score,
            "secondary": "",
            "status": "",
        },
        {
            "section": "robustness",
            "name": "parameter",
            "value": result.parameter_robustness_score,
            "secondary": "",
            "status": "",
        },
        {
            "section": "robustness",
            "name": "input",
            "value": result.input_robustness_score,
            "secondary": "",
            "status": "",
        },
        {
            "section": "robustness",
            "name": "scenario",
            "value": result.scenario_robustness_score,
            "secondary": "",
            "status": "",
        },
        {
            "section": "robustness",
            "name": "monte_carlo",
            "value": result.monte_carlo_robustness_score,
            "secondary": "",
            "status": "",
        },
        {
            "section": "robustness",
            "name": "overall",
            "value": result.overall_robustness_score,
            "secondary": "",
            "status": robustness_label(
                result.overall_robustness_score
            ),
        },
    ]

    for record in result.local_parameter_sensitivity:
        rows.append(
            {
                "section": "parameter_sensitivity",
                "name": record.name,
                "value": record.absolute_effect,
                "secondary": record.normalized_sensitivity,
                "status": "",
            }
        )

    for record in result.input_sensitivity:
        rows.append(
            {
                "section": "input_sensitivity",
                "name": record.name,
                "value": record.absolute_effect,
                "secondary": record.normalized_sensitivity,
                "status": "",
            }
        )

    for scenario in result.scenario_results:
        rows.append(
            {
                "section": "scenario",
                "name": scenario.scenario,
                "value": scenario.score,
                "secondary": scenario.delta_from_baseline,
                "status": scenario.status,
            }
        )

    fieldnames = [
        "section",
        "name",
        "value",
        "secondary",
        "status",
    ]

    path = Path(filename)

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
        writer.writerows(rows)


# ============================================================================
# SELF TESTS
# ============================================================================

def test_parameter_registry() -> None:
    registry = default_parameter_registry()

    assert len(registry) == 7

    names = {
        item.name
        for item in registry
    }

    assert "climate_weight" in names
    assert "resilience_weight" in names

    for item in registry:
        assert item.lower <= item.default
        assert item.default <= item.upper


def test_default_model() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)
    state = default_input_state()

    validate_parameters(
        parameters,
        registry,
    )

    result = evaluate(
        state,
        parameters,
    )

    assert math.isfinite(result.score)
    assert 0.0 <= result.score <= 100.0


def test_scenario_bounds() -> None:
    state = default_input_state()

    for scenario in default_scenarios():
        result = apply_scenario(
            state,
            scenario,
        )

        values = [
            result.economic_signal,
            result.climate_risk,
            result.food_security,
            result.energy_reliability,
            result.resilience,
            result.governance,
        ]

        assert all(
            0.0 <= value <= 1.0
            for value in values
        )


def test_local_parameter_sensitivity() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    records = local_parameter_sensitivity(
        default_input_state(),
        parameters,
        registry,
    )

    assert len(records) == len(registry)

    for record in records:
        assert record.absolute_effect >= 0.0


def test_input_sensitivity() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    records = input_sensitivity(
        default_input_state(),
        parameters,
    )

    assert len(records) == 6


def test_scenario_analysis() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    results = scenario_analysis(
        default_input_state(),
        parameters,
        default_scenarios(),
    )

    assert len(results) == len(
        default_scenarios()
    )

    baseline = next(
        item
        for item in results
        if item.scenario == "baseline"
    )

    assert abs(baseline.delta_from_baseline) < 1e-12


def test_monte_carlo_reproducibility() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    first = monte_carlo_robustness(
        state=default_input_state(),
        parameters=parameters,
        registry=registry,
        runs=200,
        seed=123,
    )

    second = monte_carlo_robustness(
        state=default_input_state(),
        parameters=parameters,
        registry=registry,
        runs=200,
        seed=123,
    )

    assert asdict(first) == asdict(second)


def test_monte_carlo_distribution() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    summary = monte_carlo_robustness(
        state=default_input_state(),
        parameters=parameters,
        registry=registry,
        runs=200,
        seed=42,
    )

    assert summary.runs == 200
    assert summary.minimum <= summary.mean
    assert summary.mean <= summary.maximum
    assert summary.p05 <= summary.p95
    assert summary.standard_deviation >= 0.0


def test_robustness_scores() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    result = run_gate9(
        runs=200,
        seed=42,
    )

    scores = [
        result.parameter_robustness_score,
        result.input_robustness_score,
        result.scenario_robustness_score,
        result.monte_carlo_robustness_score,
        result.overall_robustness_score,
    ]

    assert all(
        0.0 <= score <= 100.0
        for score in scores
    )

    # Make sure registry and parameters are actually exercised.
    validate_parameters(
        parameters,
        registry,
    )


def test_failure_detection() -> None:
    registry = default_parameter_registry()
    parameters = default_parameters(registry)

    result = run_gate9(
        runs=100,
        seed=42,
    )

    failures, warnings = detect_flags(
        baseline_score=result.baseline_score,
        parameter_records=result.local_parameter_sensitivity,
        input_records=result.input_sensitivity,
        scenario_results=result.scenario_results,
        monte_carlo=result.monte_carlo,
    )

    assert isinstance(failures, list)
    assert isinstance(warnings, list)


def test_fingerprint_reproducibility() -> None:
    first = run_gate9(
        runs=200,
        seed=42,
    )

    second = run_gate9(
        runs=200,
        seed=42,
    )

    assert first.fingerprint == second.fingerprint


def test_fingerprint_changes_with_seed() -> None:
    first = run_gate9(
        runs=200,
        seed=42,
    )

    second = run_gate9(
        runs=200,
        seed=43,
    )

    assert first.fingerprint != second.fingerprint


def test_json_export() -> None:
    result = run_gate9(
        runs=100,
        seed=42,
    )

    with tempfile.TemporaryDirectory() as directory:
        filename = str(
            Path(directory) / "gate9.json"
        )

        save_json(
            result,
            filename,
        )

        path = Path(filename)

        assert path.exists()

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            loaded = json.load(handle)

        assert (
            loaded["fingerprint"]
            == result.fingerprint
        )


def test_csv_export() -> None:
    result = run_gate9(
        runs=100,
        seed=42,
    )

    with tempfile.TemporaryDirectory() as directory:
        filename = str(
            Path(directory) / "gate9.csv"
        )

        save_csv(
            result,
            filename,
        )

        path = Path(filename)

        assert path.exists()
        assert path.stat().st_size > 0


def self_test() -> bool:
    """Run the complete Gate 9 test suite."""

    tests = [
        (
            "parameter registry",
            test_parameter_registry,
        ),
        (
            "default model",
            test_default_model,
        ),
        (
            "scenario bounds",
            test_scenario_bounds,
        ),
        (
            "local parameter sensitivity",
            test_local_parameter_sensitivity,
        ),
        (
            "input sensitivity",
            test_input_sensitivity,
        ),
        (
            "scenario analysis",
            test_scenario_analysis,
        ),
        (
            "Monte Carlo reproducibility",
            test_monte_carlo_reproducibility,
        ),
        (
            "Monte Carlo distribution",
            test_monte_carlo_distribution,
        ),
        (
            "robustness scores",
            test_robustness_scores,
        ),
        (
            "failure detection",
            test_failure_detection,
        ),
        (
            "fingerprint reproducibility",
            test_fingerprint_reproducibility,
        ),
        (
            "fingerprint seed sensitivity",
            test_fingerprint_changes_with_seed,
        ),
        (
            "JSON export",
            test_json_export,
        ),
        (
            "CSV export",
            test_csv_export,
        ),
    ]

    passed = 0
    failed = 0

    print()
    print("GLOBAL DIGITAL TWIN GATE 9 SELF TEST")
    print("=" * 78)

    for name, function in tests:
        try:
            function()
            print(f"PASS: {name}")
            passed += 1
        except Exception as exc:
            print(
                f"FAIL: {name} -> "
                f"{type(exc).__name__}: {exc}"
            )
            failed += 1

    print()
    print("=" * 78)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 78)

    if failed == 0:
        print("GLOBAL DIGITAL TWIN GATE 9: PASS")
        return True

    print("GLOBAL DIGITAL TWIN GATE 9: FAIL")
    return False


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Gate 9 — "
            "Sensitivity & Robustness"
        )
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run all Gate 9 self-tests.",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=1000,
        help="Monte Carlo robustness runs.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic Monte Carlo seed.",
    )

    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Export complete result to JSON.",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Export summary to CSV.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.runs < 10:
        parser.error(
            "--runs must be at least 10."
        )

    if args.self_test:
        return 0 if self_test() else 1

    result = run_gate9(
        runs=args.runs,
        seed=args.seed,
    )

    print_report(result)

    if args.json:
        save_json(
            result,
            args.json,
        )
        print()
        print(
            f"JSON written to: {args.json}"
        )

    if args.csv:
        save_csv(
            result,
            args.csv,
        )
        print(
            f"CSV written to: {args.csv}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())