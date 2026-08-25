"""
CIDAR benchmark result persistence and regression tracking.

Stores benchmark records as JSON and JSONL using only the
Python standard library.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

from .cidar_protocol import CIDARBenchmarkRecord


def save_result(
    record: CIDARBenchmarkRecord,
    path: str | Path,
) -> Path:
    """Save one benchmark record as formatted JSON."""
    if not record.valid:
        raise ValueError(
            "cannot save an invalid benchmark record"
        )

    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            asdict(record),
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    return output


def load_result(
    path: str | Path,
) -> CIDARBenchmarkRecord:
    """Load one benchmark record from JSON."""
    source = Path(path)

    data = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    return CIDARBenchmarkRecord(
        **data
    )


def append_result(
    record: CIDARBenchmarkRecord,
    path: str | Path,
) -> Path:
    """Append one benchmark record to a JSONL file."""
    if not record.valid:
        raise ValueError(
            "cannot save an invalid benchmark record"
        )

    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                asdict(record),
                sort_keys=True,
            )
            + "\n"
        )

    return output


def load_results(
    path: str | Path,
) -> list[CIDARBenchmarkRecord]:
    """Load all records from a JSONL file."""
    source = Path(path)

    if not source.exists():
        return []

    records: list[CIDARBenchmarkRecord] = []

    for line in source.read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue

        records.append(
            CIDARBenchmarkRecord(
                **json.loads(line)
            )
        )

    return records


def best_result(
    records: Iterable[CIDARBenchmarkRecord],
) -> CIDARBenchmarkRecord:
    """Return the record with the lowest RMSE."""
    values = list(records)

    if not values:
        raise ValueError(
            "at least one result is required"
        )

    invalid = [
        record
        for record in values
        if not record.valid
    ]

    if invalid:
        raise ValueError(
            "all benchmark records must be valid"
        )

    return min(
        values,
        key=lambda record: record.rmse,
    )


def compare_rmse(
    baseline: CIDARBenchmarkRecord,
    candidate: CIDARBenchmarkRecord,
) -> float:
    """
    Return relative RMSE improvement.

    Positive = candidate improved.
    Negative = candidate regressed.
    """
    if not baseline.valid:
        raise ValueError(
            "baseline must be valid"
        )

    if not candidate.valid:
        raise ValueError(
            "candidate must be valid"
        )

    if baseline.rmse == 0.0:
        return 0.0

    return (
        (baseline.rmse - candidate.rmse)
        / baseline.rmse
    )


def regression_report(
    baseline: CIDARBenchmarkRecord,
    candidate: CIDARBenchmarkRecord,
) -> str:
    """Create a benchmark regression report."""
    improvement = compare_rmse(
        baseline,
        candidate,
    )

    if improvement > 0.0:
        status = "IMPROVED"
    elif improvement < 0.0:
        status = "REGRESSED"
    else:
        status = "UNCHANGED"

    return (
        "CIDAR REGRESSION REPORT\n"
        "=======================\n"
        f"Status: {status}\n"
        f"Baseline RMSE: "
        f"{baseline.rmse:.6f} m\n"
        f"Candidate RMSE: "
        f"{candidate.rmse:.6f} m\n"
        f"Relative Improvement: "
        f"{improvement:.4%}\n"
        f"Baseline Dataset: "
        f"{baseline.dataset_name}\n"
        f"Candidate Dataset: "
        f"{candidate.dataset_name}"
    )


__all__ = [
    "append_result",
    "best_result",
    "compare_rmse",
    "load_result",
    "load_results",
    "regression_report",
    "save_result",
]