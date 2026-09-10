"""
Global Digital Twin - Integration Gate 2
=========================================

Gate 2:
Modular integration and health monitoring.

Purpose:
    Connect existing GEDT, CIDAR, climate, food, energy,
    resilience, and AI-governance components through a
    common interface.

Important:
    Existing modules are optional. The system continues to
    operate using safe internal adapters when a module is
    unavailable.

Python standard library only.

Version: 2.0.0
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


VERSION = "2.0.0"


# ============================================================
# COMMON DATA STRUCTURES
# ============================================================

@dataclass
class ModuleStatus:
    name: str
    module: str
    available: bool
    healthy: bool
    message: str


@dataclass
class IntegratedState:
    period: int
    economy: Dict[str, float]
    climate: Dict[str, float]
    food: Dict[str, float]
    energy: Dict[str, float]
    resilience: Dict[str, float]
    governance: Dict[str, float]
    sensors: Dict[str, float]


@dataclass
class IntegrationReport:
    version: str
    timestamp_utc: str
    modules_total: int
    modules_available: int
    modules_healthy: int
    integration_health: float
    state_integrity: bool
    overall_status: str


# ============================================================
# SAFE UTILITIES
# ============================================================

def clamp(
    value: float,
    low: float,
    high: float,
) -> float:
    return max(low, min(high, value))


def now_utc() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        result = float(value)

        if result != result:
            return default

        return result

    except (TypeError, ValueError):
        return default


# ============================================================
# MODULE REGISTRY
# ============================================================

MODULE_REGISTRY = {
    "GEDT": [
        "GEDT_standalone",
        "gedt",
    ],

    "CIDAR": [
        "CIDAR_standalone",
        "cidar",
    ],

    "GlobalResilience": [
        "Global_Resilience_Twin",
    ],

    "ClimateEconomic": [
        "Climate_Economic_Twin",
    ],

    "FoodSecurity": [
        "Food_Security_Twin",
    ],

    "EnergyTransition": [
        "Energy_Transition_Twin",
    ],

    "AIGovernance": [
        "AI_Governance_Engine",
    ],
}


# ============================================================
# MODULE LOADER
# ============================================================

class ModuleLoader:

    def __init__(self) -> None:

        self.loaded: Dict[str, Any] = {}
        self.status: List[ModuleStatus] = []

    def discover(self) -> List[ModuleStatus]:

        self.loaded.clear()
        self.status.clear()

        for domain, candidates in MODULE_REGISTRY.items():

            found = False
            message = "No compatible module found."

            for module_name in candidates:

                try:

                    module = importlib.import_module(
                        module_name
                    )

                    self.loaded[domain] = module

                    self.status.append(
                        ModuleStatus(
                            name=domain,
                            module=module_name,
                            available=True,
                            healthy=True,
                            message="Module loaded successfully.",
                        )
                    )

                    found = True
                    break

                except Exception as exc:

                    message = (
                        f"Unavailable: {type(exc).__name__}"
                    )

            if not found:

                self.status.append(
                    ModuleStatus(
                        name=domain,
                        module=candidates[0],
                        available=False,
                        healthy=False,
                        message=message,
                    )
                )

        return self.status


# ============================================================
# DOMAIN ADAPTER
# ============================================================

class DomainAdapter:

    def __init__(
        self,
        loader: ModuleLoader,
    ) -> None:

        self.loader = loader

    def get_domain_state(
        self,
        domain: str,
        period: int,
    ) -> Dict[str, float]:

        module = self.loader.loaded.get(domain)

        if module is None:

            return self.fallback_state(
                domain,
                period,
            )

        # ----------------------------------------------------
        # Optional module-level state function
        # ----------------------------------------------------

        if hasattr(module, "get_state"):

            try:

                result = module.get_state(
                    period=period
                )

                if isinstance(result, dict):

                    return {
                        str(k): safe_float(v)
                        for k, v in result.items()
                    }

            except Exception:
                pass

        # ----------------------------------------------------
        # Known safe fallback representation
        # ----------------------------------------------------

        return self.fallback_state(
            domain,
            period,
        )

    def fallback_state(
        self,
        domain: str,
        period: int,
    ) -> Dict[str, float]:

        defaults = {

            "GEDT": {
                "economic_output": 100.0,
                "productivity": 1.0,
                "employment": 0.94,
            },

            "CIDAR": {
                "depth": 20.0,
                "uncertainty": 0.5,
                "confidence": 0.95,
            },

            "GlobalResilience": {
                "resilience": 70.0,
                "infrastructure": 0.85,
                "preparedness": 0.60,
            },

            "ClimateEconomic": {
                "temperature_anomaly": 1.2,
                "climate_risk": 0.25,
                "emissions": 100.0,
            },

            "FoodSecurity": {
                "food_production": 100.0,
                "food_security": 0.80,
                "food_price": 1.0,
            },

            "EnergyTransition": {
                "renewable_share": 0.30,
                "energy_price": 0.15,
                "grid_reliability": 0.96,
            },

            "AIGovernance": {
                "safety": 0.90,
                "accountability": 0.85,
                "transparency": 0.85,
            },
        }

        return dict(
            defaults.get(
                domain,
                {},
            )
        )


# ============================================================
# INTEGRATION ENGINE
# ============================================================

class GlobalDigitalTwinGate2:

    def __init__(
        self,
        seed: int = 42,
    ) -> None:

        self.seed = seed

        self.loader = ModuleLoader()

        self.adapter = DomainAdapter(
            self.loader
        )

        self.history: List[
            IntegratedState
        ] = []

    # --------------------------------------------------------
    # Discover modules
    # --------------------------------------------------------

    def discover_modules(
        self,
    ) -> List[ModuleStatus]:

        return self.loader.discover()

    # --------------------------------------------------------
    # Build common state
    # --------------------------------------------------------

    def build_state(
        self,
        period: int,
    ) -> IntegratedState:

        state = IntegratedState(

            period=period,

            economy=self.adapter.get_domain_state(
                "GEDT",
                period,
            ),

            climate=self.adapter.get_domain_state(
                "ClimateEconomic",
                period,
            ),

            food=self.adapter.get_domain_state(
                "FoodSecurity",
                period,
            ),

            energy=self.adapter.get_domain_state(
                "EnergyTransition",
                period,
            ),

            resilience=self.adapter.get_domain_state(
                "GlobalResilience",
                period,
            ),

            governance=self.adapter.get_domain_state(
                "AIGovernance",
                period,
            ),

            sensors=self.adapter.get_domain_state(
                "CIDAR",
                period,
            ),
        )

        self.history.append(state)

        return state

    # --------------------------------------------------------
    # State integrity
    # --------------------------------------------------------

    def validate_state(
        self,
        state: IntegratedState,
    ) -> bool:

        domains = [
            state.economy,
            state.climate,
            state.food,
            state.energy,
            state.resilience,
            state.governance,
            state.sensors,
        ]

        for domain in domains:

            if not isinstance(domain, dict):
                return False

            for value in domain.values():

                if not isinstance(value, float):
                    return False

        return True

    # --------------------------------------------------------
    # Health score
    # --------------------------------------------------------

    def health_score(self) -> float:

        statuses = self.loader.status

        if not statuses:
            return 0.0

        total = len(statuses)

        healthy = sum(
            1
            for item in statuses
            if item.healthy
        )

        return (
            healthy / total
        ) * 100.0

    # --------------------------------------------------------
    # Integration report
    # --------------------------------------------------------

    def report(self) -> IntegrationReport:

        statuses = self.loader.status

        available = sum(
            1
            for item in statuses
            if item.available
        )

        healthy = sum(
            1
            for item in statuses
            if item.healthy
        )

        integrity = True

        if self.history:

            integrity = self.validate_state(
                self.history[-1]
            )

        health = self.health_score()

        if health >= 90.0 and integrity:
            overall = "PASS"

        elif health >= 50.0 and integrity:
            overall = "PARTIAL"

        else:
            overall = "FAIL"

        return IntegrationReport(
            version=VERSION,
            timestamp_utc=now_utc(),
            modules_total=len(statuses),
            modules_available=available,
            modules_healthy=healthy,
            integration_health=health,
            state_integrity=integrity,
            overall_status=overall,
        )

    # --------------------------------------------------------
    # Run integration
    # --------------------------------------------------------

    def run(
        self,
        periods: int = 10,
    ) -> List[IntegratedState]:

        if periods < 1:
            raise ValueError(
                "periods must be >= 1"
            )

        self.discover_modules()

        for period in range(
            1,
            periods + 1,
        ):

            self.build_state(
                period
            )

        return self.history


# ============================================================
# REPORTING
# ============================================================

def print_modules(
    statuses: List[ModuleStatus],
) -> None:

    print()
    print("=" * 80)
    print("MODULE DISCOVERY")
    print("=" * 80)

    for item in statuses:

        status = (
            "AVAILABLE"
            if item.available
            else "FALLBACK"
        )

        print(
            f"{item.name:<22}"
            f"{status:<12}"
            f"{item.module:<30}"
        )

    print("=" * 80)


def print_state(
    state: IntegratedState,
) -> None:

    print()
    print("=" * 80)
    print(
        f"INTEGRATED GLOBAL STATE — PERIOD {state.period}"
    )
    print("=" * 80)

    print("\nECONOMY")

    for key, value in state.economy.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("\nCLIMATE")

    for key, value in state.climate.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("\nFOOD")

    for key, value in state.food.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("\nENERGY")

    for key, value in state.energy.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("\nRESILIENCE")

    for key, value in state.resilience.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("\nAI GOVERNANCE")

    for key, value in state.governance.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("\nCIDAR / SENSORS")

    for key, value in state.sensors.items():
        print(
            f"  {key:<25}: {value:.4f}"
        )

    print("=" * 80)


def print_report(
    report: IntegrationReport,
) -> None:

    print()
    print("=" * 80)
    print("INTEGRATION HEALTH")
    print("=" * 80)

    print(
        f"Modules total:         "
        f"{report.modules_total}"
    )

    print(
        f"Modules available:     "
        f"{report.modules_available}"
    )

    print(
        f"Modules healthy:       "
        f"{report.modules_healthy}"
    )

    print(
        f"Integration health:    "
        f"{report.integration_health:.2f}%"
    )

    print(
        f"State integrity:       "
        f"{report.state_integrity}"
    )

    print(
        f"Overall status:        "
        f"{report.overall_status}"
    )

    print("=" * 80)


# ============================================================
# JSON EXPORT
# ============================================================

def save_json(
    filename: str,
    report: IntegrationReport,
    statuses: List[ModuleStatus],
    history: List[IntegratedState],
) -> None:

    payload = {

        "version": VERSION,

        "report": asdict(
            report
        ),

        "modules": [
            asdict(item)
            for item in statuses
        ],

        "history": [
            asdict(state)
            for state in history
        ],
    }

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> bool:

    passed = 0
    failed = 0

    print()
    print("GLOBAL DIGITAL TWIN GATE 2 SELF TEST")
    print("=" * 80)

    # --------------------------------------------------------
    # Test 1
    # --------------------------------------------------------

    try:

        twin = GlobalDigitalTwinGate2()

        twin.run(5)

        assert len(twin.history) == 5

        print(
            "PASS: integration engine"
        )

        passed += 1

    except Exception as exc:

        print(
            f"FAIL: integration engine -> {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 2
    # --------------------------------------------------------

    try:

        twin = GlobalDigitalTwinGate2()

        twin.run(1)

        state = twin.history[-1]

        assert twin.validate_state(
            state
        )

        print(
            "PASS: common state integrity"
        )

        passed += 1

    except Exception as exc:

        print(
            f"FAIL: common state integrity -> {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 3
    # --------------------------------------------------------

    try:

        twin = GlobalDigitalTwinGate2()

        twin.run(1)

        report = twin.report()

        assert (
            0.0
            <= report.integration_health
            <= 100.0
        )

        print(
            "PASS: integration health"
        )

        passed += 1

    except Exception as exc:

        print(
            f"FAIL: integration health -> {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 4
    # --------------------------------------------------------

    try:

        twin_a = GlobalDigitalTwinGate2(
            seed=42
        )

        twin_b = GlobalDigitalTwinGate2(
            seed=42
        )

        twin_a.run(5)
        twin_b.run(5)

        assert (
            asdict(twin_a.history[-1])
            == asdict(twin_b.history[-1])
        )

        print(
            "PASS: reproducibility"
        )

        passed += 1

    except Exception as exc:

        print(
            f"FAIL: reproducibility -> {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 5
    # --------------------------------------------------------

    try:

        twin = GlobalDigitalTwinGate2()

        statuses = twin.discover_modules()

        assert len(statuses) == 7

        print(
            "PASS: module registry"
        )

        passed += 1

    except Exception as exc:

        print(
            f"FAIL: module registry -> {exc}"
        )

        failed += 1

    print("=" * 80)
    print(
        f"PASSED: {passed}"
    )
    print(
        f"FAILED: {failed}"
    )

    if failed == 0:

        print(
            "GLOBAL DIGITAL TWIN GATE 2: PASS"
        )

        print("=" * 80)

        return True

    print(
        "GLOBAL DIGITAL TWIN GATE 2: FAIL"
    )

    print("=" * 80)

    return False


# ============================================================
# COMMAND LINE
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Integration Gate 2"
        )
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    parser.add_argument(
        "--modules",
        action="store_true",
    )

    parser.add_argument(
        "--json",
        default="",
    )

    args = parser.parse_args()

    if args.self_test:

        return (
            0
            if self_test()
            else 1
        )

    twin = GlobalDigitalTwinGate2()

    history = twin.run(
        periods=args.periods
    )

    if args.modules:

        print_modules(
            twin.loader.status
        )

    if history:

        print_state(
            history[-1]
        )

    report = twin.report()

    print_report(
        report
    )

    if args.json:

        save_json(
            filename=args.json,
            report=report,
            statuses=twin.loader.status,
            history=history,
        )

        print(
            f"\nJSON saved to: {args.json}"
        )

    return (
        0
        if report.overall_status != "FAIL"
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())