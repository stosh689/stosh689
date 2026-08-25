"""Persistence and comparison of CIDAR benchmark results."""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Iterable, Sequence

from .cidar_protocol import CIDARBenchmarkRecord


def _from_dict(
    payload: dict,
) -> CIDARBenchmarkRecord:
    data = dict(payload)
    data["sensors"] = tuple(
        data.get("sensors", ())
    )

    allowed = {
        field.name
        for field in fields(
            CIDARBenchmarkRecord
        )
    }

    return CIDARBenchmarkRecord(
        **{
            key: value
            for key, value in data.items()
            if key in allowed
        }
    )


def save_result(
    record: CIDARBenchmarkRecord,
    path: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            record.to_dict(),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def load_result(
    path: str | Path,
) -> CIDARBenchmarkRecord:
    path = Path(path)

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return _from_dict(payload)


def append_result(
    record: CIDARBenchmarkRecord,
    path: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                record.to_dict(),
                sort_keys=True,
            )
            + "\n"
        )


def load_results(
    path: str | Path,
) -> list[CIDARBenchmarkRecord]:
    path = Path(path)

    results: list[CIDARBenchmarkRecord] = []

    if not path.exists():
        return results

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            results.append(
                _from_dict(
                    json.loads(line)
                )
            )

    return results


def best_result(
    records: Sequence[CIDARBenchmarkRecord],
) -> CIDARBenchmarkRecord:
    if not records:
        raise ValueError(
            "records cannot be empty"
        )

    return min(
        records,
        key=lambda record: record.rmse,
    )


def compare_rmse(
    baseline: CIDARBenchmarkRecord,
    candidate: CIDARBenchmarkRecord,
) -> float:
    return (
        baseline.rmse
        - candidate.rmse
    )


def regression_report(
    baseline: CIDARBenchmarkRecord,
    candidate: CIDARBenchmarkRecord,
) -> str:
    improvement = compare_rmse(
        baseline,
        candidate,
    )

    status = (
        "IMPROVED"
        if improvement > 0
        else (
            "REGRESSED"
            if improvement < 0
            else "UNCHANGED"
        )
    )

    return (
        "CIDAR REGRESSION REPORT\n"
        "=======================\n"
        f"Baseline RMSE: "
        f"{baseline.rmse:.6f}\n"
        f"Candidate RMSE: "
        f"{candidate.rmse:.6f}\n"
        f"RMSE Improvement: "
        f"{improvement:.6f}\n"
        f"Status: {status}\n"
    )


__all__ = [
    "save_result",
    "load_result",
    "append_result",
    "load_results",
    "best_result",
    "compare_rmse",
    "regression_report",
]