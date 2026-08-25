from pathlib import Path

import pytest

from gedt.cidar_adapters import (
    CSVDepthAdapter,
    JSONDepthAdapter,
    JSONLDepthAdapter,
    load_with_adapter,
    validate_samples,
)
from gedt.cidar_dataset import DepthSample


def test_csv_adapter(tmp_path: Path):
    path = tmp_path / "data.csv"

    path.write_text(
        "ground_truth,prediction,sample_id\n"
        "5.0,5.1,a\n"
        "10.0,9.9,b\n",
        encoding="utf-8",
    )

    samples = load_with_adapter(
        CSVDepthAdapter(),
        path,
    )

    assert len(samples) == 2
    assert samples[0].sample_id == "a"


def test_json_adapter(tmp_path: Path):
    path = tmp_path / "data.json"

    path.write_text(
        '[{"ground_truth": 5, "prediction": 5.1}]',
        encoding="utf-8",
    )

    samples = load_with_adapter(
        JSONDepthAdapter(),
        path,
    )

    assert len(samples) == 1


def test_jsonl_adapter(tmp_path: Path):
    path = tmp_path / "data.jsonl"

    path.write_text(
        '{"ground_truth": 5, "prediction": 5.1}\n',
        encoding="utf-8",
    )

    samples = load_with_adapter(
        JSONLDepthAdapter(),
        path,
    )

    assert len(samples) == 1


def test_validate_samples():
    samples = validate_samples(
        [
            DepthSample(
                ground_truth=10.0,
                prediction=10.2,
            )
        ]
    )

    assert len(samples) == 1


def test_empty_samples_rejected():
    with pytest.raises(ValueError):
        validate_samples([])


def test_negative_ground_truth_rejected():
    with pytest.raises(ValueError):
        validate_samples(
            [
                DepthSample(
                    ground_truth=-1.0,
                    prediction=1.0,
                )
            ]
        )


def test_negative_prediction_rejected():
    with pytest.raises(ValueError):
        validate_samples(
            [
                DepthSample(
                    ground_truth=1.0,
                    prediction=-1.0,
                )
            ]
        )