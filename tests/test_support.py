"""Shared lightweight HTTP response test double."""

from __future__ import annotations


class FakeResponse:
    """Minimal requests.Response-compatible object for tests."""

    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = int(status_code)
        self._json_data = json_data
        self.text = text

        if isinstance(text, str):
            self.content = text.encode("utf-8")
        else:
            self.content = text

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")