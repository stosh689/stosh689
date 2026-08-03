# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] - 2026-07-03

### Added (Section E — Future Plans implementation)

- `scripts/ai_analysis.py` — AI-based analysis module:
  - `cluster_countries()` — KMeans clustering on indicator data
  - `detect_trends()` — linear-regression slope per country over time
  - `correlation_matrix()` — pairwise Pearson correlations between indicators
  - `summarize()` — full analysis pipeline
- `scripts/dashboard.py` — multi-panel matplotlib dashboard:
  - `build_dashboard()` — bar chart + scatter + correlation heatmap
  - `save_dashboard()` — export to PNG
- `scripts/worldbank_fetch.py` — multi-indicator support:
  - `INDICATORS` catalogue (energy use, CO₂ emissions, renewable %, GDP/capita, population)
  - `fetch_multiple_indicators()` — fetch several indicators at once
  - `compare_indicators()` — country × indicator pivot table
- `tests/test_ai_analysis.py` — 9 tests (clustering, trends, correlation, summarize)
- `tests/test_dashboard.py` — 3 tests (figure build, save, single-indicator edge case)
- `tests/test_worldbank_fetch.py` — 3 new tests (multi-indicator fetch, compare, default year)

### Added (Section A–D)

- `scripts/` package containing the four code snippets from `CODE.md`, refactored into importable, testable functions:
  - `scripts/translate.py` — `translate_word()` (googletrans, lazy import)
  - `scripts/translate_requests.py` — `translate_text()` + `build_url()` (requests)
  - `scripts/worldbank_fetch.py` — `fetch_data()`, `process_data()`, `plot_top_countries()`
  - `scripts/resource_manager.py` — full SQLite resource manager
- `tests/` package with 29 pytest unit tests covering all four scripts:
  - `tests/conftest.py` — shared fixtures (`FakeTranslator`, `FakeResponse`, `tmp_db`)
  - `tests/test_translate.py`, `test_translate_requests.py`, `test_worldbank_fetch.py`, `test_resource_manager.py`
- `.github/instructions/TODO.md` — task plan tracking this work.
- `CHANGELOG.md` — this file.

### Changed

- `scripts/resource_manager.py` (from `CODE.md` snippet 4) — completed the previously incomplete script:
  - Added `update_resource()`, `delete_resource()`, `get_resource()`, `search_resources()`.
  - Added input validation for `name`, `quantity`, and `status`.
  - Made all functions accept a `db_name` parameter (no longer hardcoded).
  - Replaced manual connect/close with a `_connect()` context manager.
- `scripts/worldbank_fetch.py` — `process_data()` now extracts the country name from the World Bank API's nested `{"value": ...}` dict structure.
- `scripts/worldbank_fetch.py` (Section E) — `process_data()` now accepts a `value_label` parameter; `plot_top_countries()` auto-detects the value column; `main()` uses the `INDICATORS` label.
- `CODE.md` — summary table now points at `scripts/`; added a section documenting the experimental root-level `.py` files; added `ai_analysis.py` + `dashboard.py` rows.
- `ARCHITECTURE.md` — added "Root-Level Python Files" section with per-file status, dependency graph, and recommended cleanup; marked all Future Plans items as done; updated module guide table, directory tree, and dependencies table.

### Fixed

- `googletrans` top-level import broke on Python 3.14 (`httpx` → removed `cgi` module). Fixed by making the import lazy inside `translate_word()`.
- `worldbank_fetch.process_data()` retained the `country` field as a dict, causing downstream plot failures. Fixed by extracting the `value` key.
