#!/usr/bin/env python3
"""
Global Digital Twin - Integration Gate 4
========================================

Objective:
    Establish a common, validated data contract between all
    Global Digital Twin domains.

Domains:
    Economy
    Climate
    Food
    Energy
    Disaster / Resilience
    AI Governance
    Sensors / CIDAR

Gate 4 introduces:

    1. CommonState
    2. DomainSnapshot
    3. Data validation
    4. Cross-domain state exchange
    5. Event propagation
    6. Deterministic fingerprints
    7. JSON serialization
    8. Built-in self-tests

Standard library only.

Version: 4.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


VERSION = "4.0.0"


# ============================================================
# CONSTANTS
# ============================================================

DOMAINS = (
    "economy",
    "climate",
    "food",
    "energy",
    "resilience",
    "governance",
    "sensors",
)


# ============================================================
# BASIC VALIDATION
# ============================================================

def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


# ============================================================
# DOMAIN SNAPSHOT
# ============================================================

@dataclass
class DomainSnapshot:
    """
    Standard representation of one domain's state.
    """

    domain: str
    period: int
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "VALID"
    source: str = "Gate4"
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> List[str]:

        errors = []

        if self.domain not in DOMAINS:
            errors.append(f"Unknown domain: {self.domain}")

        if self.period < 0:
            errors.append("Period must be non-negative.")

        if not isinstance(self.metrics, dict):
            errors.append("Metrics must be a dictionary.")

        else:

            for key, value in self.metrics.items():

                if not isinstance(key, str):
                    errors.append("Metric names must be strings.")

                if not finite(value):
                    errors.append(
                        f"Metric '{key}' is not finite."
                    )

        return errors


# ============================================================
# COMMON GLOBAL STATE
# ============================================================

@dataclass
class CommonState:
    """
    Cross-domain state contract.

    Every integrated simulation period produces exactly one
    CommonState object.
    """

    period: int

    economy: DomainSnapshot
    climate: DomainSnapshot
    food: DomainSnapshot
    energy: DomainSnapshot
    resilience: DomainSnapshot
    governance: DomainSnapshot
    sensors: DomainSnapshot

    events: List[Dict[str, Any]] = field(default_factory=list)

    global_score: float = 0.0

    schema_version: str = "1.0"

    def snapshots(self) -> List[DomainSnapshot]:
        return [
            self.economy,
            self.climate,
            self.food,
            self.energy,
            self.resilience,
            self.governance,
            self.sensors,
        ]

    def validate(self) -> List[str]:

        errors = []

        if self.period < 0:
            errors.append("Invalid global period.")

        expected = set(DOMAINS)

        actual = {
            snapshot.domain
            for snapshot in self.snapshots()
        }

        missing = expected - actual

        if missing:
            errors.append(
                f"Missing domains: {sorted(missing)}"
            )

        for snapshot in self.snapshots():
            errors.extend(snapshot.validate())

        if not finite(self.global_score):
            errors.append("Global score is not finite.")

        return errors

    def fingerprint(self) -> str:

        payload = asdict(self)

        payload.pop("events", None)

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()


# ============================================================
# EVENT SYSTEM
# ============================================================

@dataclass
class SystemEvent:
    """
    Cross-domain event.

    Events allow one domain to influence another without
    directly coupling their internal implementation.
    """

    event_id: str
    period: int
    source: str
    event_type: str
    severity: float
    description: str
    effects: Dict[str, float] = field(default_factory=dict)

    def validate(self) -> List[str]:

        errors = []

        if not self.event_id:
            errors.append("Missing event ID.")

        if self.source not in DOMAINS:
            errors.append(
                f"Invalid event source: {self.source}"
            )

        if not finite(self.severity):
            errors.append("Event severity is invalid.")

        if not 0.0 <= self.severity <= 100.0:
            errors.append(
                "Event severity must be between 0 and 100."
            )

        for key, value in self.effects.items():

            if not isinstance(key, str):
                errors.append("Effect names must be strings.")

            if not finite(value):
                errors.append(
                    f"Invalid effect value: {key}"
                )

        return errors


class EventBus:

    def __init__(self):
        self.events: List[SystemEvent] = []

    def publish(self, event: SystemEvent) -> None:

        errors = event.validate()

        if errors:
            raise ValueError(
                "Invalid event: " + "; ".join(errors)
            )

        self.events.append(event)

    def events_for_period(self, period: int) -> List[SystemEvent]:

        return [
            event
            for event in self.events
            if event.period == period
        ]

    def clear(self) -> None:
        self.events.clear()


# ============================================================
# COMMON DATA CONTRACT
# ============================================================

class DataContract:

    def __init__(self):
        self.schema_version = "1.0"

    def validate_snapshot(
        self,
        snapshot: DomainSnapshot,
    ) -> bool:

        return len(snapshot.validate()) == 0

    def validate_global_state(
        self,
        state: CommonState,
    ) -> bool:

        return len(state.validate()) == 0

    def serialize(
        self,
        state: CommonState,
    ) -> Dict[str, Any]:

        errors = state.validate()

        if errors:
            raise ValueError(
                "Cannot serialize invalid state: "
                + "; ".join(errors)
            )

        return asdict(state)

    def json(
        self,
        state: CommonState,
    ) -> str:

        return json.dumps(
            self.serialize(state),
            indent=2,
            sort_keys=True,
        )


# ============================================================
# DOMAIN FACTORY
# ============================================================

class DomainFactory:

    @staticmethod
    def economy(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="economy",
            period=period,
            metrics={
                "gdp": 100.0,
                "growth": 2.0,
                "employment": 95.0,
                "human_capital": 60.0,
                "inequality": 35.0,
            },
        )

    @staticmethod
    def climate(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="climate",
            period=period,
            metrics={
                "temperature_change": 1.2,
                "emissions": 50.0,
                "climate_risk": 25.0,
                "adaptation": 40.0,
            },
        )

    @staticmethod
    def food(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="food",
            period=period,
            metrics={
                "production": 100.0,
                "availability": 95.0,
                "food_price": 100.0,
                "security": 80.0,
            },
        )

    @staticmethod
    def energy(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="energy",
            period=period,
            metrics={
                "renewables": 35.0,
                "reliability": 96.0,
                "energy_price": 100.0,
                "emissions": 45.0,
            },
        )

    @staticmethod
    def resilience(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="resilience",
            period=period,
            metrics={
                "infrastructure": 80.0,
                "preparedness": 70.0,
                "response": 75.0,
                "recovery": 72.0,
            },
        )

    @staticmethod
    def governance(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="governance",
            period=period,
            metrics={
                "safety": 90.0,
                "transparency": 88.0,
                "accountability": 87.0,
                "human_oversight": 92.0,
            },
        )

    @staticmethod
    def sensors(period: int) -> DomainSnapshot:

        return DomainSnapshot(
            domain="sensors",
            period=period,
            metrics={
                "coverage": 85.0,
                "confidence": 90.0,
                "data_quality": 92.0,
                "fusion_quality": 88.0,
            },
        )


# ============================================================
# GLOBAL STATE BUILDER
# ============================================================

class StateBuilder:

    def __init__(self, seed: int = 42):

        self.random = random.Random(seed)

    def build(self, period: int) -> CommonState:

        state = CommonState(
            period=period,
            economy=DomainFactory.economy(period),
            climate=DomainFactory.climate(period),
            food=DomainFactory.food(period),
            energy=DomainFactory.energy(period),
            resilience=DomainFactory.resilience(period),
            governance=DomainFactory.governance(period),
            sensors=DomainFactory.sensors(period),
        )

        self.calculate_global_score(state)

        return state

    def calculate_global_score(
        self,
        state: CommonState,
    ) -> float:

        values = [
            state.economy.metrics["employment"],
            state.climate.metrics["adaptation"],
            state.food.metrics["security"],
            state.energy.metrics["reliability"],
            state.resilience.metrics["preparedness"],
            state.governance.metrics["safety"],
            state.sensors.metrics["data_quality"],
        ]

        state.global_score = clamp(
            sum(values) / len(values)
        )

        return state.global_score


# ============================================================
# CROSS-DOMAIN EXCHANGE
# ============================================================

class CrossDomainExchange:

    """
    Applies controlled relationships between domains.

    This is deliberately simple at Gate 4.

    Later gates can replace these rules with calibrated
    empirical/ML relationships.
    """

    def apply(
        self,
        state: CommonState,
        events: List[SystemEvent],
    ) -> CommonState:

        # ----------------------------------------------------
        # Climate -> Agriculture
        # ----------------------------------------------------

        climate_risk = state.climate.metrics["climate_risk"]

        state.food.metrics["security"] -= (
            climate_risk * 0.03
        )

        state.food.metrics["production"] -= (
            climate_risk * 0.02
        )

        # ----------------------------------------------------
        # Energy -> Economy
        # ----------------------------------------------------

        energy_reliability = (
            state.energy.metrics["reliability"]
        )

        state.economy.metrics["employment"] += (
            energy_reliability - 90.0
        ) * 0.02

        # ----------------------------------------------------
        # Climate -> Energy
        # ----------------------------------------------------

        state.energy.metrics["emissions"] *= (
            1.0 - (
                state.energy.metrics["renewables"] / 1000.0
            )
        )

        # ----------------------------------------------------
        # Governance -> System resilience
        # ----------------------------------------------------

        governance = state.governance.metrics

        governance_quality = (
            governance["safety"]
            + governance["transparency"]
            + governance["accountability"]
            + governance["human_oversight"]
        ) / 4.0

        state.resilience.metrics["preparedness"] += (
            governance_quality - 75.0
        ) * 0.03

        # ----------------------------------------------------
        # Sensors -> Response
        # ----------------------------------------------------

        sensor_quality = (
            state.sensors.metrics["confidence"]
            + state.sensors.metrics["data_quality"]
            + state.sensors.metrics["fusion_quality"]
        ) / 3.0

        state.resilience.metrics["response"] += (
            sensor_quality - 75.0
        ) * 0.03

        # ----------------------------------------------------
        # Events
        # ----------------------------------------------------

        for event in events:

            if event.source == "climate":

                state.food.metrics["production"] -= (
                    event.severity * 0.10
                )

                state.energy.metrics["reliability"] -= (
                    event.severity * 0.05
                )

                state.economy.metrics["growth"] -= (
                    event.severity * 0.02
                )

            elif event.source == "energy":

                state.economy.metrics["growth"] -= (
                    event.severity * 0.03
                )

                state.food.metrics["food_price"] += (
                    event.severity * 0.04
                )

            elif event.source == "disaster":

                state.resilience.metrics["infrastructure"] -= (
                    event.severity * 0.15
                )

                state.resilience.metrics["response"] -= (
                    event.severity * 0.10
                )

                state.economy.metrics["employment"] -= (
                    event.severity * 0.05
                )

        self._bound_state(state)

        return state

    def _bound_state(
        self,
        state: CommonState,
    ) -> None:

        bounded_metrics = {
            "employment",
            "human_capital",
            "inequality",
            "climate_risk",
            "adaptation",
            "availability",
            "security",
            "renewables",
            "reliability",
            "infrastructure",
            "preparedness",
            "response",
            "recovery",
            "safety",
            "transparency",
            "accountability",
            "human_oversight",
            "coverage",
            "confidence",
            "data_quality",
            "fusion_quality",
        }

        for snapshot in state.snapshots():

            for key, value in list(
                snapshot.metrics.items()
            ):

                if key in bounded_metrics:
                    snapshot.metrics[key] = clamp(value)


# ============================================================
# INTEGRATED SIMULATION
# ============================================================

class Gate4Engine:

    def __init__(self, seed: int = 42):

        self.seed = seed
        self.random = random.Random(seed)

        self.contract = DataContract()
        self.events = EventBus()
        self.builder = StateBuilder(seed)
        self.exchange = CrossDomainExchange()

        self.history: List[CommonState] = []

    def generate_events(
        self,
        period: int,
    ) -> None:

        # Controlled deterministic probability.

        if self.random.random() < 0.15:

            event = SystemEvent(
                event_id=f"CLIMATE-{period}",
                period=period,
                source="climate",
                event_type="climate_stress",
                severity=25.0,
                description="Moderate climate stress event.",
            )

            self.events.publish(event)

        if self.random.random() < 0.10:

            event = SystemEvent(
                event_id=f"ENERGY-{period}",
                period=period,
                source="energy",
                event_type="energy_disruption",
                severity=20.0,
                description="Temporary energy disruption.",
            )

            self.events.publish(event)

        if self.random.random() < 0.08:

            event = SystemEvent(
                event_id=f"DISASTER-{period}",
                period=period,
                source="disaster",
                event_type="infrastructure_shock",
                severity=30.0,
                description="Infrastructure disruption.",
            )

            self.events.publish(event)

    def run(
        self,
        periods: int = 10,
    ) -> List[CommonState]:

        periods = max(1, int(periods))

        self.history.clear()

        for period in range(periods):

            state = self.builder.build(period)

            self.generate_events(period)

            current_events = self.events.events_for_period(
                period
            )

            self.exchange.apply(
                state,
                current_events,
            )

            self.builder.calculate_global_score(
                state
            )

            state.events = [
                asdict(event)
                for event in current_events
            ]

            errors = state.validate()

            if errors:
                raise ValueError(
                    f"Invalid state at period {period}: "
                    + "; ".join(errors)
                )

            self.history.append(state)

        return self.history

    def summary(self) -> Dict[str, Any]:

        if not self.history:
            return {
                "status": "NO_DATA"
            }

        scores = [
            state.global_score
            for state in self.history
        ]

        return {
            "periods": len(self.history),
            "initial_score": round(scores[0], 4),
            "final_score": round(scores[-1], 4),
            "average_score": round(
                sum(scores) / len(scores),
                4,
            ),
            "minimum_score": round(
                min(scores),
                4,
            ),
            "maximum_score": round(
                max(scores),
                4,
            ),
            "final_fingerprint": self.history[-1].fingerprint(),
        }


# ============================================================
# REPORT
# ============================================================

def print_report(
    history: List[CommonState],
    summary: Dict[str, Any],
) -> None:

    print()
    print("=" * 72)
    print("GLOBAL DIGITAL TWIN — GATE 4")
    print("COMMON DATA CONTRACT + CROSS-DOMAIN STATE EXCHANGE")
    print("=" * 72)

    print()
    print(f"Version:          {VERSION}")
    print(f"Periods:          {len(history)}")
    print(f"Initial score:    {summary.get('initial_score', 0):.2f}")
    print(f"Final score:      {summary.get('final_score', 0):.2f}")
    print(f"Average score:    {summary.get('average_score', 0):.2f}")

    print()
    print("-" * 72)
    print("PERIOD STATES")
    print("-" * 72)

    for state in history:

        print(
            f"Period {state.period:3d} | "
            f"Global Score: {state.global_score:6.2f} | "
            f"Events: {len(state.events):2d} | "
            f"Fingerprint: {state.fingerprint()[:12]}"
        )

    print()
    print("=" * 72)


# ============================================================
# JSON EXPORT
# ============================================================

def save_json(
    history: List[CommonState],
    filename: str,
) -> None:

    payload = {
        "version": VERSION,
        "states": [
            asdict(state)
            for state in history
        ],
    }

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> int:

    print()
    print("GLOBAL DIGITAL TWIN GATE 4 SELF TEST")
    print("=" * 72)

    passed = 0
    failed = 0

    # --------------------------------------------------------
    # Test 1
    # --------------------------------------------------------

    try:

        snapshot = DomainFactory.economy(0)

        assert snapshot.domain == "economy"
        assert snapshot.validate() == []

        print("PASS: domain snapshot contract")
        passed += 1

    except Exception as exc:

        print(f"FAIL: domain snapshot contract — {exc}")
        failed += 1

    # --------------------------------------------------------
    # Test 2
    # --------------------------------------------------------

    try:

        builder = StateBuilder(seed=42)
        state = builder.build(0)

        assert state.validate() == []
        assert len(state.snapshots()) == 7

        print("PASS: common global state")
        passed += 1

    except Exception as exc:

        print(f"FAIL: common global state — {exc}")
        failed += 1

    # --------------------------------------------------------
    # Test 3
    # --------------------------------------------------------

    try:

        event = SystemEvent(
            event_id="TEST-1",
            period=0,
            source="climate",
            event_type="test",
            severity=10.0,
            description="Test event.",
        )

        assert event.validate() == []

        bus = EventBus()
        bus.publish(event)

        assert len(bus.events_for_period(0)) == 1

        print("PASS: event bus")
        passed += 1

    except Exception as exc:

        print(f"FAIL: event bus — {exc}")
        failed += 1

    # --------------------------------------------------------
    # Test 4
    # --------------------------------------------------------

    try:

        engine = Gate4Engine(seed=42)
        history = engine.run(periods=5)

        assert len(history) == 5

        for state in history:
            assert state.validate() == []

        print("PASS: cross-domain exchange")
        passed += 1

    except Exception as exc:

        print(f"FAIL: cross-domain exchange — {exc}")
        failed += 1

    # --------------------------------------------------------
    # Test 5
    # --------------------------------------------------------

    try:

        engine_a = Gate4Engine(seed=123)
        engine_b = Gate4Engine(seed=123)

        history_a = engine_a.run(5)
        history_b = engine_b.run(5)

        fingerprints_a = [
            state.fingerprint()
            for state in history_a
        ]

        fingerprints_b = [
            state.fingerprint()
            for state in history_b
        ]

        assert fingerprints_a == fingerprints_b

        print("PASS: deterministic reproducibility")
        passed += 1

    except Exception as exc:

        print(f"FAIL: reproducibility — {exc}")
        failed += 1

    # --------------------------------------------------------
    # Test 6
    # --------------------------------------------------------

    try:

        engine = Gate4Engine(seed=42)
        history = engine.run(3)

        contract = DataContract()

        for state in history:

            encoded = contract.json(state)

            decoded = json.loads(encoded)

            assert decoded["schema_version"] == "1.0"
            assert "economy" in decoded
            assert "climate" in decoded
            assert "food" in decoded
            assert "energy" in decoded

        print("PASS: JSON data contract")
        passed += 1

    except Exception as exc:

        print(f"FAIL: JSON contract — {exc}")
        failed += 1

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 72)

    if failed == 0:

        print("GLOBAL DIGITAL TWIN GATE 4: PASS")
        return 0

    print("GLOBAL DIGITAL TWIN GATE 4: REVIEW")
    return 1


# ============================================================
# CLI
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Integration Gate 4"
        )
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=10,
        help="Number of simulation periods.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in tests.",
    )

    parser.add_argument(
        "--json",
        type=str,
        default="",
        help="Write simulation to JSON.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=VERSION,
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    engine = Gate4Engine(
        seed=args.seed
    )

    history = engine.run(
        periods=args.periods
    )

    summary = engine.summary()

    print_report(
        history,
        summary,
    )

    if args.json:

        save_json(
            history,
            args.json,
        )

        print()
        print(
            f"JSON report written to: {args.json}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())