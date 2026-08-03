"""Tests for scripts/translate_requests.py."""

from scripts import translate_requests
from tests.conftest import FakeResponse


def _make_fetcher(json_data, status_code=200):
    """Return a fetcher callable that ignores params."""
    def fetcher(url, params=None):
        return FakeResponse(status_code=status_code, json_data=json_data)
    return fetcher


def test_translate_text_success():
    # Google web API shape: [[[translated, original, ...], ...], ...]
    json_data = [[["Hola, mundo!", "Hello, world!", None, None]]]
    fetcher = _make_fetcher(json_data)
    results = translate_requests.translate_text(
        text="Hello, world!",
        languages=["es"],
        fetcher=fetcher,
    )
    assert results == {"es": "Hola, mundo!"}


def test_translate_text_multiple_languages():
    json_data = [[["Bonjour", "Hello, world!", None, None]]]
    fetcher = _make_fetcher(json_data)
    results = translate_requests.translate_text(
        languages=["fr", "de"], fetcher=fetcher
    )
    assert results == {"fr": "Bonjour", "de": "Bonjour"}


def test_translate_text_error_status():
    fetcher = _make_fetcher(None, status_code=500)
    results = translate_requests.translate_text(
        languages=["es"], fetcher=fetcher
    )
    assert results == {"es": "Error 500"}


def test_build_url():
    url, params = translate_requests.build_url("hi", "es")
    assert url == translate_requests.BASE_URL
    assert params["tl"] == "es"
    assert params["q"] == "hi"
    assert params["client"] == "gtx"


def test_translate_text_default_languages():
    json_data = [[["X", "Hello, world!", None, None]]]
    fetcher = _make_fetcher(json_data)
    results = translate_requests.translate_text(fetcher=fetcher)
    assert set(results.keys()) == set(translate_requests.LANGUAGES)
