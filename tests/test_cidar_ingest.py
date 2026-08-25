from pathlib import Path

from gedt.cidar_dataset import DepthSample
from gedt.cidar_ingest import (
    CIDARDataError,
    load_csv,
    load_dataset,
    load_json,
    load_jsonl,
    save_jsonl,
)


def test_load_csv(tmp_path: Path):
    path = tmp_path / "samples.csv"

    path.write_text(
        "ground_truth,prediction,sample_id\n"
        "10.0,10.2,a\n"
        "20.0,19.8,b\n",
        encoding="utf-8",
    )

    samples = load_csv(path)

    assert len(samples) == 2
    assert samples[0].ground_truth == 10.0
    assert samples[0].prediction == 10.2
    assert samples[0].sample_id == "a"


def test_load_json(tmp_path: Path):
    path = tmp_path / "samples.json"

    path.write_text(
        '[{"ground_truth": 10, '
        '"prediction": 10.1, '
        '"sample_id": "frame-1"}]',
        encoding="utf-8",
    )

    samples = load_json(path)

    assert len(samples) == 1
    assert samples[0].ground_truth == 10.0
    assert samples[0].prediction == 10.1
    assert samples[0].sample_id == "frame-1"


def test_load_json_wrapped_samples(tmp_path: Path):
    path = tmp_path / "samples.json"

    path.write_text(
        '{"samples": ['
        '{"ground_truth": 5, "prediction": 5.1}'
        ']}',
        encoding="utf-8",
    )

    samples = load_json(path)

    assert len(samples) == 1
    assert samples[0].ground_truth == 5.0
    assert samples[0].prediction == 5.1


def test_load_jsonl(tmp_path: Path):
    path = tmp_path / "samples.jsonl"

    path.write_text(
        '{"ground_truth": 5, "prediction": 5.1}\n'
        '{"ground_truth": 10, "prediction": 9.8}\n',
        encoding="utf-8",
    )

    samples = load_jsonl(path)

    assert len(samples) == 2
    assert samples[0].ground_truth == 5.0
    assert samples[1].prediction == 9.8


def test_load_dataset_csv(tmp_path: Path):
    path = tmp_path / "samples.csv"

    path.write_text(
        "ground_truth,prediction\n"
        "10,10.2\n",
        encoding="utf-8",
    )

    samples = load_dataset(path)

    assert len(samples) == 1
    assert samples[0].ground_truth == 10.0


def test_load_dataset_json(tmp_path: Path):
    path = tmp_path / "samples.json"

    path.write_text(
        '[{"ground_truth": 10, "prediction": 10.2}]',
        encoding="utf-8",
    )

    samples = load_dataset(path)

    assert len(samples) == 1


def test_load_dataset_jsonl(tmp_path: Path):
    path = tmp_path / "samples.jsonl"

    path.write_text(
        '{"ground_truth": 10, "prediction": 10.2}\n',
        encoding="utf-8",
    )

    samples = load_dataset(path)

    assert len(samples) == 1


def test_save_and_reload_jsonl(tmp_path: Path):
    source = [
        DepthSample(
            ground_truth=1.0,
            prediction=1.1,
            sample_id="a",
        ),
        DepthSample(
            ground_truth=2.0,
            prediction=1.9,
            sample_id="b",
        ),
    ]

    path = tmp_path / "saved.jsonl"

    save_jsonl(source, path)

    loaded = load_jsonl(path)

    assert loaded == source


def test_missing_ground_truth(tmp_path: Path):
    path = tmp_path / "bad.jsonl"

    path.write_text(
        '{"prediction": 10.0}\n',
        encoding="utf-8",
    )

    try:
        load_jsonl(path)
    except CIDARDataError:
        pass
    else:
        raise AssertionError(
            "Expected CIDARDataError"
        )


def test_missing_prediction(tmp_path: Path):
    path = tmp_path / "bad.jsonl"

    path.write_text(
        '{"ground_truth": 10.0}\n',
        encoding="utf-8",
    )

    try:
        load_jsonl(path)
    except CIDARDataError:
        pass
    else:
        raise AssertionError(
            "Expected CIDARDataError"
        )


def test_missing_csv_column(tmp_path: Path):
    path = tmp_path / "bad.csv"

    path.write_text(
        "ground_truth\n"
        "10\n",
        encoding="utf-8",
    )

    try:
        load_csv(path)
    except CIDARDataError:
        pass
    else:
        raise AssertionError(
            "Expected CIDARDataError"
        )


def test_unsupported_format(tmp_path: Path):
    path = tmp_path / "samples.txt"

    path.write_text(
        "data",
        encoding="utf-8",
    )

    try:
        load_dataset(path)
    except CIDARDataError:
        pass
    else:
        raise AssertionError(
            "Expected CIDARDataError"
        )