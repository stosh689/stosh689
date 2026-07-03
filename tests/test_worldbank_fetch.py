"""Tests for scripts/worldbank_fetch.py."""

import pytest

from scripts import worldbank_fetch
from tests.conftest import FakeResponse


def _sample_records():
    return [
        {"country": {"id": "X", "value": "CountryA"},
            "value": 100.0, "date": "2020"},
        {"country": {"id": "Y", "value": "CountryB"}, "value": 50.0, "date": "2020"},
        {"country": {"id": "Z", "value": "CountryC"}, "value": None, "date": "2020"},
    ]


def test_fetch_data_success():
    json_data = [{"meta": {}}, _sample_records()]
    def fetcher(url, params=None): return FakeResponse(200, json_data)
    records = worldbank_fetch.fetch_data(fetcher=fetcher)
    assert len(records) == 3
    assert records[0]["country"]["value"] == "CountryA"


def test_fetch_data_no_records():
    json_data = [{"meta": {}}]
    def fetcher(url, params=None): return FakeResponse(200, json_data)
    records = worldbank_fetch.fetch_data(fetcher=fetcher)
    assert records == []


def test_fetch_data_http_error():
    def fetcher(url, params=None): return FakeResponse(503, {})
    with pytest.raises(ConnectionError, match="503"):
        worldbank_fetch.fetch_data(fetcher=fetcher)


def test_process_data_drops_na_and_sorts():
    df = worldbank_fetch.process_data(_sample_records())
    assert len(df) == 2  # one row had value=None
    # sorted descending by value
    assert df.iloc[0]["Country"] == "CountryA"
    assert df.iloc[1]["Country"] == "CountryB"


def test_process_data_columns():
    df = worldbank_fetch.process_data(_sample_records())
    assert list(df.columns) == ["Country", "Value", "Year"]


def test_process_data_custom_label():
    df = worldbank_fetch.process_data(
        _sample_records(), value_label="My Indicator")
    assert "My Indicator" in df.columns


def test_plot_top_countries(tmp_path):
    df = worldbank_fetch.process_data(_sample_records())
    save_path = tmp_path / "chart.png"
    worldbank_fetch.plot_top_countries(df, n=2, save_path=str(save_path))
    assert save_path.exists()
    assert save_path.stat().st_size > 0


# --- multi-indicator support (E1) ---
def _indicator_records(country, value, year="2020"):
    return [{"country": {"id": "X", "value": country}, "value": value, "date": year}]


def test_fetch_multiple_indicators():
    indicators = {
        "EG.USE.PCAP.KG.OE": "Energy Use",
        "EN.ATM.CO2E.PC": "CO2 Emissions",
    }
    # fetcher returns different data depending on URL (indicator code in URL)

    def fetcher(url, params=None):
        if "EG.USE" in url:
            data = [{"meta": {}}, _indicator_records("CountryA", 100.0)]
        else:
            data = [{"meta": {}}, _indicator_records("CountryA", 5.0)]
        return FakeResponse(200, data)

    result = worldbank_fetch.fetch_multiple_indicators(
        indicators, fetcher=fetcher)
    assert set(result.keys()) == {"Energy Use", "CO2 Emissions"}
    assert result["Energy Use"].iloc[0]["Country"] == "CountryA"


def test_compare_indicators():
    import pandas as pd

    indicator_dfs = {
        "Energy Use": pd.DataFrame({
            "Country": ["A", "B"], "Year": ["2020", "2020"], "Energy Use": [100.0, 50.0],
        }),
        "CO2 Emissions": pd.DataFrame({
            "Country": ["A", "B"], "Year": ["2020", "2020"], "CO2 Emissions": [5.0, 3.0],
        }),
    }
    pivot = worldbank_fetch.compare_indicators(indicator_dfs, year=2020)
    assert list(pivot.columns) == ["Energy Use", "CO2 Emissions"]
    assert pivot.loc["A", "Energy Use"] == 100.0
    assert pivot.loc["B", "CO2 Emissions"] == 3.0


def test_compare_indicators_default_year():
    import pandas as pd

    indicator_dfs = {
        "Energy Use": pd.DataFrame({
            "Country": ["A"], "Year": ["2020"], "Energy Use": [100.0],
        }),
    }
    pivot = worldbank_fetch.compare_indicators(indicator_dfs)
    assert "A" in pivot.index
