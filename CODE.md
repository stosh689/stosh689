# Python Code Snippets

This document collects all Python code examples from the project.

## 1. Multi-Language Translation (Google Translate API)

Translates the word **"sampilin"** into ~60 languages using the `googletrans` library.

```python
from googletrans import Translator

translator = Translator()

word = "sampilin"

languages = [
    "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs",
    "bg", "ca", "ceb", "ny", "zh-cn", "zh-tw", "co", "hr", "cs",
    "da", "nl", "en", "eo", "et", "fi", "fr", "fy", "gl", "ka",
    "de", "el", "gu", "ht", "ha", "haw", "he", "hi", "hmn", "hu",
    "is", "ig", "id", "ga", "it", "ja", "jw", "kn", "kk", "km",
    "rw", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk",
    "mg", "ms", "ml"
]

for lang in languages:
    translation = translator.translate(word, dest=lang)
    print(f"{lang}: {translation.text}")
```

## 2. Translation Script Using `requests`

Translates **"Hello, world!"** into 15 languages using the Google Translate web API via the `requests` library.

```python
import requests

text = "Hello, world!"

languages = [
    "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh-CN",
    "ar", "hi", "bn", "tr", "nl", "sv"
]

for lang in languages:
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q={text}"
    response = requests.get(url)
    if response.status_code == 200:
        translated_text = response.json()[0][0][0]
        print(f"{lang}: {translated_text}")
    else:
        print(f"{lang}: Error {response.status_code}")
```

## 3. World Bank Data Fetcher

Fetches **energy use per capita** (indicator: `EG.USE.PCAP.KG.OE`) from the World Bank's World Development Indicators API and processes it with `pandas`.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

# World Bank API endpoint
indicator = "EG.USE.PCAP.KG.OE"
url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=10000"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # The World Bank API returns a list: [meta, data_records]
    if len(data) > 1:
        records = data[1]

        # Convert to DataFrame
        df = pd.DataFrame(records)

        # Select relevant columns
        df = df[["country", "value", "date"]]
        df.columns = ["Country", "Energy Use (kg of oil equivalent per capita)", "Year"]

        # Drop rows with missing values
        df = df.dropna()

        # Sort by energy use (descending)
        df = df.sort_values(by="Energy Use (kg of oil equivalent per capita)", ascending=False)

        # Display top 20
        print(df.head(20))

        # Plot top 20 countries
        top_20 = df.head(20)
        plt.figure(figsize=(12, 6))
        plt.barh(top_20["Country"], top_20["Energy Use (kg of oil equivalent per capita)"])
        plt.xlabel("Energy Use (kg of oil equivalent per capita)")
        plt.title("Top 20 Countries by Energy Use Per Capita")
        plt.tight_layout()
        plt.savefig("energy_use_top20.png", dpi=150)
        plt.show()
    else:
        print("No data records returned.")
else:
    print(f"API request failed with status code: {response.status_code}")
```

## 4. SQLite Resource Manager (Incomplete)

> ⚠️ **Note:** This script is incomplete and contains syntax errors. It is a work in progress.

```python
import sqlite3

def create_database(db_name="resources.db"):
    """Create a SQLite database for tracking resources."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER DEFAULT 0,
            location TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{db_name}' created successfully.")

def add_resource(name, category, quantity, location):
    """Add a new resource to the database."""
    conn = sqlite3.connect("resources.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO resources (name, category, quantity, location)
        VALUES (?, ?, ?, ?)
    ''', (name, category, quantity, location))

    conn.commit()
    conn.close()
    print(f"Resource '{name}' added.")

def view_resources():
    """View all resources in the database."""
    conn = sqlite3.connect("resources.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM resources")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()

# TODO: Add update_resource() and delete_resource() functions
# TODO: Add search/filter functionality
# TODO: Add error handling and input validation

if __name__ == "__main__":
    create_database()
    # add_resource("Water Filters", "Humanitarian", 500, "Warehouse A")
    # view_resources()
```

## Summary of Code Files

> **Note:** The four scripts above now live in [`scripts/`](./scripts/) and have been refactored for testability. `resource_manager.py` is now complete with full CRUD, search, and validation. Unit tests are in [`tests/`](./tests/) — run with `pytest tests/ -v`.

| Script                          | Library Used                       | Status      | Purpose                                                     |
| ------------------------------- | ---------------------------------- | ----------- | ----------------------------------------------------------- |
| `scripts/translate.py`          | `googletrans`                      | ✅ Working  | Translate a word into ~60 languages                         |
| `scripts/translate_requests.py` | `requests`                         | ✅ Working  | Translate "Hello, world!" into 15 languages                 |
| `scripts/worldbank_fetch.py`    | `requests`, `pandas`, `matplotlib` | ✅ Working  | Fetch multiple indicators from World Bank API + compare     |
| `scripts/resource_manager.py`   | `sqlite3`                          | ✅ Complete | SQLite-based resource tracking (CRUD + search + validation) |
| `scripts/ai_analysis.py`        | `scikit-learn`, `numpy`, `pandas`  | ✅ Working  | KMeans clustering, trend detection, correlation matrix      |
| `scripts/dashboard.py`          | `matplotlib`, `numpy`              | ✅ Working  | Multi-panel dashboard (bar + scatter + heatmap)             |

## Root-Level Python Files (Experimental / Untracked)

These files are **not** in `scripts/` — they are experimental prototypes at the repo root. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for full details and known issues.

| File                       | Purpose                                                   | Status                                                 |
| -------------------------- | --------------------------------------------------------- | ------------------------------------------------------ |
| `cidar.py`                 | Crisis-management model (LogReg + ethical + resource opt) | ⚠️ Duplicate of `training_plan.py`; broken import      |
| `training_plan.py`         | Crisis-management model                                   | ⚠️ Duplicate of `cidar.py`; broken import              |
| `crisis_management .py`    | Full crisis pipeline (train + ethical + optimize)         | ⚠️ Filename has trailing space; reads missing CSV      |
| `realtime.py`              | `ethical_decision()` scorer                               | ⚠️ Filename mismatch (should be `ethical_decision.py`) |
| `resource_optimization.py` | `optimize_resources()` via LP                             | ⚠️ Ignores input param; hardcoded values               |
| `ml_model.py`              | `prepare_data()` + `evaluate_model()`                     | ⚠️ Broken import; reads missing CSV                    |
| `atomically correct.py`    | Markdown doc (intergalactic_communication skeleton)       | ⚠️ Not valid Python; filename has space                |
