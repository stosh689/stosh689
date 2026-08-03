"""Shared pytest fixtures."""

import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Make scripts/ importable
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))


class FakeTranslation:
    """Mimics googletrans.Translator.translate() return value."""

    def __init__(self, text):
        self.text = text


class FakeTranslator:
    """Fake googletrans Translator that maps lang -> translated text."""

    def __init__(self, mapping=None):
        self.mapping = mapping or {}

    def translate(self, word, dest):
        return FakeTranslation(self.mapping.get(dest, f"[{dest}]{word}"))


class FakeResponse:
    """Fake requests.Response."""

    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}

    def json(self):
        return self._json


@pytest.fixture
def fake_translator():
    return FakeTranslator


@pytest.fixture
def fake_response():
    return FakeResponse


@pytest.fixture
def tmp_db():
    """Create a fresh resource DB in a temp file, yield path, then clean up."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # let resource_manager create it
    yield path
    if os.path.exists(path):
        os.remove(path)
