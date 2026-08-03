"""Fetch development-indicator data from the World Bank API and visualise it."""

import requests
import pandas as pd
import matplotlib.pyplot as plt

INDICATOR = "EG.USE.PCAP.KG.OE"
API_URL = "http://api.worldbank.org/v2/country/all/indicator/{indicator}"

# Catalogue of supported indicators (code -> human-readable label).
INDICATORS = {
    "EG.USE.PCAP.KG.OE": "Energy Use (kg of oil equivalent per capita)",
    "EN.ATM.CO2E.PC": "CO2 Emissions (metric tons per capita)",
    "EG.FEC.RNEW.ZS": "Renewable Energy (% of total final energy consumption)",
    "NY.GDP.PCAP.CD": "GDP per Capita (current US$)",
    "SP.POP.TOTL": "Population, total",
}


def fetch_data(indicator=INDICATOR, per_page=10000, fetcher=None):
    """Fetch raw records from the World Bank API.

    *fetcher* is an optional callable ``(url)`` -> requests.Response for testing.
    Returns the list of data records (may be empty).
    """
    if fetcher is None:
        fetcher = requests.get

    url = API_URL.format(indicator=indicator)
    params = {"format": "json", "per_page": per_page}
    response = fetcher(
        url, params=params) if "params" in fetcher.__code__.co_varnames else fetcher(url)

    if response.status_code != 200:
        raise ConnectionError(
            f"API request failed with status code: {response.status_code}")

    data = response.json()
    if len(data) <= 1:
        return []
    return data[1]


def process_data(records, value_label=None):
    """Convert raw API records into a cleaned, sorted DataFrame.

    *value_label* overrides the column name for the ``value`` field
    (defaults to the generic ``"Value"``).
    """
    df = pd.DataFrame(records)
    # World Bank API returns country as {"id": ..., "value": "CountryName"}
    if "country" in df.columns and df["country"].apply(lambda x: isinstance(x, dict)).any():
        df["country"] = df["country"].apply(
            lambda x: x.get("value", x) if isinstance(x, dict) else x
        )
    df = df[["country", "value", "date"]]
    df.columns = ["Country", value_label or "Value", "Year"]
    df = df.dropna()
    df = df.sort_values(by=value_label or "Value", ascending=False)
    return df


def fetch_multiple_indicators(indicators=None, fetcher=None):
    """Fetch several indicators and return a dict {label: DataFrame}.

    *indicators* is a ``{code: label}`` mapping (defaults to ``INDICATORS``).
    """
    if indicators is None:
        indicators = INDICATORS
    results = {}
    for code, label in indicators.items():
        records = fetch_data(indicator=code, fetcher=fetcher)
        if records:
            results[label] = process_data(records, value_label=label)
    return results


def compare_indicators(indicator_dfs, year=None):
    """Build a country × indicator pivot table from multiple indicator DataFrames.

    *indicator_dfs* is a ``{label: DataFrame}`` mapping (output of
    ``fetch_multiple_indicators``).  *year* filters to a single year
    (defaults to the most recent year present across all indicators).
    """
    frames = []
    for label, df in indicator_dfs.items():
        value_col = [c for c in df.columns if c not in ("Country", "Year")][0]
        sub = df[["Country", "Year", value_col]].copy()
        sub = sub.rename(columns={value_col: label})
        frames.append(sub)

    merged = frames[0]
    for frame in frames[1:]:
        merged = pd.merge(merged, frame, on=["Country", "Year"], how="outer")

    if year is None:
        # pick the most recent year with data across the most indicators
        year = int(merged["Year"].dropna().astype(int).max())
    merged = merged[merged["Year"].astype(int) == year].drop(columns=["Year"])
    merged = merged.set_index("Country")
    return merged


def plot_top_countries(df, n=20, save_path=None):
    """Plot the top *n* countries by the DataFrame's value column.

    If *save_path* is given the figure is saved instead of shown.
    """
    value_col = [c for c in df.columns if c not in ("Country", "Year")][0]
    top = df.head(n)
    plt.figure(figsize=(12, 6))
    plt.barh(top["Country"], top[value_col])
    plt.xlabel(value_col)
    plt.title(f"Top {n} Countries by {value_col}")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    else:
        plt.show()
    plt.close()


def main():
    records = fetch_data()
    if not records:
        print("No data records returned.")
        return
    df = process_data(records, value_label=INDICATORS[INDICATOR])
    print(df.head(20))
    plot_top_countries(df, save_path="energy_use_top20.png")


if __name__ == "__main__":
    main()
