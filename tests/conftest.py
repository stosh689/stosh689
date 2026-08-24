"""
Shared pytest configuration and lightweight HTTP response test double.
This file intentionally contains only test infrastructure.
It does not modify production code.
"""
from __future__ import annotations
class FakeResponse:
    """Minimal requests.Response-compatible object for tests."""
    def __init__(
        self,
        status_code: int = 200,
        json_data=None,
        text="",
    ):
        self.status_code = int(status_code)
        self._json_data = json_data
        self.text = text
        if isinstance(text, str):
            self.content = text.encode("utf-8")
        else:
            self.content = text
    def json(self):
        """Return the configured JSON payload."""
        return self._json_data
    def raise_for_status(self):
        """Raise an error for HTTP error responses."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")