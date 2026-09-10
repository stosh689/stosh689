#!/usr/bin/env python3
"""
AI Governance Engine
====================

Gate 1 — Governance Core

A standalone framework for evaluating AI decisions using:

    - Safety
    - Transparency
    - Accountability
    - Fairness
    - Privacy
    - Sustainability
    - Human oversight
    - Risk assessment
    - Audit logging

No external dependencies.

Run:
    python AI_Governance_Engine.py

Self-test:
    python AI_Governance_Engine.py --self-test

Example:
    python AI_Governance_Engine.py --demo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Dict, List


VERSION = "1.0.0"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class AIRequest:
    request_id: str
    system: str
    action: str
    domain: str

    safety: float
    transparency: float
    accountability: float
    fairness: float
    privacy: float
    sustainability: float
    human_oversight: float

    potential_harm: float
    reversibility: float


@dataclass
class GovernanceDecision:
    request_id: str
    decision: str
    risk_level: str
    governance_score: float
    risk_score: float
    human_review_required: bool
    reasons: List[str]


@dataclass
class AuditRecord:
    timestamp: float
    request_id: str
    decision: str
    governance_score: float
    risk_score: float
    risk_level: str
    record_hash: str


# ============================================================
# UTILITIES
# ============================================================

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def weighted_average(
    values: Dict[str, float],
    weights: Dict[str, float],
) -> float:

    numerator = 0.0
    denominator = 0.0

    for key, value in values.items():

        weight = weights.get(key, 0.0)

        numerator += value * weight
        denominator += weight

    if denominator == 0:
        return 0.0

    return numerator / denominator


# ============================================================
# GOVERNANCE ENGINE
# ============================================================

class AIGovernanceEngine:

    def __init__(self):

        self.audit_log: List[AuditRecord] = []

        self.weights = {
            "safety": 0.25,
            "transparency": 0.10,
            "accountability": 0.15,
            "fairness": 0.15,
            "privacy": 0.10,
            "sustainability": 0.05,
            "human_oversight": 0.20,
        }

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def validate_request(
        self,
        request: AIRequest,
    ) -> List[str]:

        errors = []

        fields = {
            "safety": request.safety,
            "transparency": request.transparency,
            "accountability": request.accountability,
            "fairness": request.fairness,
            "privacy": request.privacy,
            "sustainability": request.sustainability,
            "human_oversight": request.human_oversight,
            "potential_harm": request.potential_harm,
            "reversibility": request.reversibility,
        }

        for name, value in fields.items():

            if not 0.0 <= value <= 100.0:
                errors.append(
                    f"{name} must be between 0 and 100"
                )

        if not request.system.strip():
            errors.append("system is required")

        if not request.action.strip():
            errors.append("action is required")

        if not request.domain.strip():
            errors.append("domain is required")

        return errors

    # --------------------------------------------------------
    # GOVERNANCE SCORE
    # --------------------------------------------------------

    def governance_score(
        self,
        request: AIRequest,
    ) -> float:

        values = {
            "safety": request.safety,
            "transparency": request.transparency,
            "accountability": request.accountability,
            "fairness": request.fairness,
            "privacy": request.privacy,
            "sustainability": request.sustainability,
            "human_oversight": request.human_oversight,
        }

        return clamp(
            weighted_average(
                values,
                self.weights,
            )
        )

    # --------------------------------------------------------
    # RISK SCORE
    # --------------------------------------------------------

    def risk_score(
        self,
        request: AIRequest,
    ) -> float:

        governance = self.governance_score(
            request
        )

        weakness = 100.0 - governance

        irreversibility = (
            100.0 - request.reversibility
        )

        risk = (
            request.potential_harm * 0.45
            + weakness * 0.30
            + irreversibility * 0.25
        )

        return clamp(risk)

    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    def risk_level(
        self,
        score: float,
    ) -> str:

        if score < 20:
            return "LOW"

        if score < 40:
            return "MODERATE"

        if score < 70:
            return "HIGH"

        return "CRITICAL"

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    def evaluate(
        self,
        request: AIRequest,
    ) -> GovernanceDecision:

        errors = self.validate_request(
            request
        )

        if errors:

            return GovernanceDecision(
                request_id=request.request_id,
                decision="REJECT",
                risk_level="INVALID",
                governance_score=0.0,
                risk_score=100.0,
                human_review_required=True,
                reasons=errors,
            )

        governance = self.governance_score(
            request
        )

        risk = self.risk_score(
            request
        )

        level = self.risk_level(
            risk
        )

        reasons = []

        human_review = False

        # ----------------------------------------------------
        # SAFETY
        # ----------------------------------------------------

        if request.safety < 60:
            reasons.append(
                "Safety score is below minimum threshold."
            )

        # ----------------------------------------------------
        # FAIRNESS
        # ----------------------------------------------------

        if request.fairness < 60:
            reasons.append(
                "Fairness score requires improvement."
            )

        # ----------------------------------------------------
        # PRIVACY
        # ----------------------------------------------------

        if request.privacy < 60:
            reasons.append(
                "Privacy protection is insufficient."
            )

        # ----------------------------------------------------
        # TRANSPARENCY
        # ----------------------------------------------------

        if request.transparency < 60:
            reasons.append(
                "Transparency is below governance threshold."
            )

        # ----------------------------------------------------
        # ACCOUNTABILITY
        # ----------------------------------------------------

        if request.accountability < 60:
            reasons.append(
                "Accountability mechanisms are insufficient."
            )

        # ----------------------------------------------------
        # HUMAN OVERSIGHT
        # ----------------------------------------------------

        if request.human_oversight < 70:
            human_review = True

            reasons.append(
                "Human oversight should be strengthened."
            )

        # ----------------------------------------------------
        # HIGH RISK
        # ----------------------------------------------------

        if risk >= 70:

            decision = "REJECT"

            human_review = True

            reasons.append(
                "Risk exceeds critical governance threshold."
            )

        elif risk >= 40:

            decision = "REVIEW"

            human_review = True

            reasons.append(
                "Human review required before deployment."
            )

        elif governance < 70:

            decision = "REVIEW"

            human_review = True

            reasons.append(
                "Governance score requires additional review."
            )

        else:

            decision = "APPROVE"

            if not reasons:
                reasons.append(
                    "Governance requirements satisfied."
                )

        result = GovernanceDecision(
            request_id=request.request_id,
            decision=decision,
            risk_level=level,
            governance_score=round(
                governance,
                4,
            ),
            risk_score=round(
                risk,
                4,
            ),
            human_review_required=human_review,
            reasons=reasons,
        )

        self.record_audit(
            result
        )

        return result

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    def record_audit(
        self,
        decision: GovernanceDecision,
    ) -> None:

        payload = (
            f"{decision.request_id}|"
            f"{decision.decision}|"
            f"{decision.governance_score}|"
            f"{decision.risk_score}|"
            f"{decision.risk_level}"
        )

        record_hash = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

        self.audit_log.append(
            AuditRecord(
                timestamp=time.time(),
                request_id=decision.request_id,
                decision=decision.decision,
                governance_score=decision.governance_score,
                risk_score=decision.risk_score,
                risk_level=decision.risk_level,
                record_hash=record_hash,
            )
        )

    # --------------------------------------------------------
    # AUDIT VERIFICATION
    # --------------------------------------------------------

    def verify_audit_log(self) -> bool:

        for record in self.audit_log:

            payload = (
                f"{record.request_id}|"
                f"{record.decision}|"
                f"{record.governance_score}|"
                f"{record.risk_score}|"
                f"{record.risk_level}"
            )

            expected = hashlib.sha256(
                payload.encode("utf-8")
            ).hexdigest()

            if expected != record.record_hash:
                return False

        return True

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    def export_audit(
        self,
        filename: str,
    ) -> None:

        data = [
            asdict(record)
            for record in self.audit_log
        ]

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
            )


# ============================================================
# DEMO REQUESTS
# ============================================================

def demo_requests() -> List[AIRequest]:

    return [

        AIRequest(
            request_id=str(uuid.uuid4()),
            system="GEDT",
            action="economic scenario analysis",
            domain="economic research",
            safety=95,
            transparency=90,
            accountability=95,
            fairness=90,
            privacy=95,
            sustainability=90,
            human_oversight=90,
            potential_harm=10,
            reversibility=95,
        ),

        AIRequest(
            request_id=str(uuid.uuid4()),
            system="Example AI",
            action="automated employment decision",
            domain="employment",
            safety=70,
            transparency=55,
            accountability=60,
            fairness=50,
            privacy=65,
            sustainability=80,
            human_oversight=50,
            potential_harm=65,
            reversibility=60,
        ),

        AIRequest(
            request_id=str(uuid.uuid4()),
            system="High Risk AI",
            action="irreversible high-impact decision",
            domain="critical services",
            safety=30,
            transparency=25,
            accountability=30,
            fairness=25,
            privacy=35,
            sustainability=40,
            human_oversight=20,
            potential_harm=95,
            reversibility=10,
        ),
    ]


# ============================================================
# REPORTING
# ============================================================

def print_decision(
    request: AIRequest,
    result: GovernanceDecision,
) -> None:

    print()
    print("-" * 70)
    print(f"System:       {request.system}")
    print(f"Action:       {request.action}")
    print(f"Domain:       {request.domain}")
    print()
    print(f"Decision:     {result.decision}")
    print(f"Risk level:   {result.risk_level}")
    print(
        f"Governance:   {result.governance_score:.2f}/100"
    )
    print(
        f"Risk score:   {result.risk_score:.2f}/100"
    )
    print(
        f"Human review: "
        f"{'YES' if result.human_review_required else 'NO'}"
    )
    print()
    print("Reasons:")

    for reason in result.reasons:
        print(f"  - {reason}")


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> bool:

    engine = AIGovernanceEngine()

    passed = 0
    failed = 0

    print()
    print("AI GOVERNANCE ENGINE SELF TEST")
    print("=" * 60)

    # Test 1
    try:

        request = demo_requests()[0]

        result = engine.evaluate(
            request
        )

        assert result.decision == "APPROVE"

        print("PASS: low-risk approval")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: low-risk approval — {exc}"
        )

        failed += 1

    # Test 2
    try:

        request = demo_requests()[1]

        result = engine.evaluate(
            request
        )

        assert result.decision in {
            "REVIEW",
            "REJECT",
        }

        assert result.human_review_required

        print("PASS: elevated-risk review")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: elevated-risk review — {exc}"
        )

        failed += 1

    # Test 3
    try:

        request = demo_requests()[2]

        result = engine.evaluate(
            request
        )

        assert result.decision == "REJECT"
        assert result.risk_level == "CRITICAL"

        print("PASS: critical-risk rejection")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: critical-risk rejection — {exc}"
        )

        failed += 1

    # Test 4
    try:

        request = demo_requests()[0]

        engine.evaluate(request)

        assert engine.verify_audit_log()

        print("PASS: audit integrity")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: audit integrity — {exc}"
        )

        failed += 1

    # Test 5
    try:

        bad_request = AIRequest(
            request_id="invalid-test",
            system="",
            action="",
            domain="",
            safety=150,
            transparency=50,
            accountability=50,
            fairness=50,
            privacy=50,
            sustainability=50,
            human_oversight=50,
            potential_harm=50,
            reversibility=50,
        )

        result = engine.evaluate(
            bad_request
        )

        assert result.decision == "REJECT"
        assert result.risk_level == "INVALID"

        print("PASS: invalid input rejection")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: invalid input rejection — {exc}"
        )

        failed += 1

    print("=" * 60)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    if failed == 0:

        print(
            "AI GOVERNANCE ENGINE SELF TEST: PASS"
        )

        return True

    print(
        "AI GOVERNANCE ENGINE SELF TEST: FAIL"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description="AI Governance Engine"
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in tests.",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run governance demonstration.",
    )

    parser.add_argument(
        "--audit",
        type=str,
        default="",
        help="Export audit log to JSON.",
    )

    args = parser.parse_args()

    if args.self_test:

        return 0 if self_test() else 1

    engine = AIGovernanceEngine()

    requests = demo_requests()

    if args.demo or not args.audit:

        print()
        print("=" * 70)
        print("AI GOVERNANCE ENGINE")
        print(f"Version: {VERSION}")
        print("=" * 70)

        for request in requests:

            result = engine.evaluate(
                request
            )

            print_decision(
                request,
                result,
            )

        print()
        print("=" * 70)
        print(
            "AUDIT LOG INTEGRITY:",
            "PASS"
            if engine.verify_audit_log()
            else "FAIL",
        )
        print("=" * 70)

    else:

        for request in requests:
            engine.evaluate(request)

    if args.audit:

        engine.export_audit(
            args.audit
        )

        print(
            f"Audit log saved: {args.audit}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())