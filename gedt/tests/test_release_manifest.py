from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "RELEASE_MANIFEST.json"


def load_manifest() -> dict:
    assert MANIFEST.exists(), "RELEASE_MANIFEST.json is missing"

    data = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    assert isinstance(data, dict)
    return data


def test_manifest_exists():
    assert MANIFEST.exists()


def test_manifest_is_valid_json():
    data = load_manifest()
    assert isinstance(data, dict)


def test_project_identity():
    data = load_manifest()

    assert data["project"] == "GEDT"
    assert data["version"] == "11.0.0"
    assert data["release_candidate"] == "RC1"


def test_release_type():
    data = load_manifest()

    assert data["release_type"] == "research_development"


def test_license():
    data = load_manifest()

    assert data["license"] == "MIT"


def test_release_requirements():
    data = load_manifest()

    requirements = data["release_requirements"]

    expected = {
        "core_engine",
        "data_pipeline",
        "automated_testing",
        "reproducibility",
        "documentation",
        "scientific_evaluation",
        "performance_benchmark",
        "release_gate",
        "continuous_integration",
    }

    assert expected.issubset(requirements.keys())

    for requirement in expected:
        assert requirements[requirement] is True


def test_baseline_configuration():
    data = load_manifest()

    baseline = data["baseline_experiment"]

    assert baseline["periods"] == 12
    assert baseline["trials"] == 1000
    assert baseline["seed"] == 42
    assert baseline["initial_gdp"] == 1000.0
    assert baseline["initial_inflation"] == 0.02
    assert baseline["initial_unemployment"] == 0.05


def test_scenario_set():
    data = load_manifest()

    scenarios = data["scenario_set"]

    expected = {
        "baseline",
        "demand_expansion",
        "demand_contraction",
        "supply_disruption",
        "supply_improvement",
        "tight_policy",
        "accommodative_policy",
    }

    assert set(scenarios) == expected


def test_quality_targets():
    data = load_manifest()

    targets = data["quality_targets"]

    assert targets["minimum_test_pass_rate_percent"] == 90.0
    assert targets["release_test_pass_rate_percent"] == 100.0
    assert targets["minimum_release_gate_checks"] == 10
    assert targets["required_release_gate_passes"] == 10
    assert targets["known_critical_runtime_failures"] == 0


def test_required_files_exist():
    data = load_manifest()

    missing = []

    for relative_path in data["required_files"]:
        path = ROOT / relative_path

        if not path.exists():
            missing.append(relative_path)

    assert not missing, (
        "Manifest lists missing files: "
        + ", ".join(missing)
    )


def test_test_directory_exists():
    data = load_manifest()

    test_directory = ROOT / data["test_directory"]

    assert test_directory.exists()
    assert test_directory.is_dir()


def test_ci_workflow_exists():
    data = load_manifest()

    workflow = ROOT.parent / data["ci_workflow"]

    assert workflow.exists()
    assert workflow.is_file()


def test_scientific_position():
    data = load_manifest()

    position = data["scientific_position"]

    assert position["predicts_real_economy"] is False
    assert position["supports_scenario_analysis"] is True
    assert position["supports_uncertainty_analysis"] is True
    assert position["supports_reproducible_experiments"] is True
    assert position["requires_empirical_validation"] is True
    assert position["requires_real_world_data_validation"] is True


def test_ethical_requirements():
    data = load_manifest()

    ethics = data["ethical_requirements"]

    for value in ethics.values():
        assert value is True


def test_release_status_is_pending_verification():
    data = load_manifest()

    status = data["release_status"]

    assert status["status"] == "PENDING_VERIFICATION"
    assert status["release_gate_required"] is True
    assert status["ci_required"] is True
    assert status["manual_approval_required"] is True


def test_release_principle_exists():
    data = load_manifest()

    principle = data["release_principle"]

    assert isinstance(principle, str)
    assert len(principle.strip()) > 20


def test_project_motto_exists():
    data = load_manifest()

    assert (
        data["project_motto"]
        == "Create. Grow. Succeed. — Together."
    )


def test_manifest_is_reproducible_json():
    data = load_manifest()

    serialized = json.dumps(
        data,
        sort_keys=True,
        indent=2,
    )

    restored = json.loads(serialized)

    assert restored == data