"""
Small HTTP-response test double used by GEDT integration tests.

This is intentionally isolated from tests/conftest.py so that existing
test infrastructure does not need to be replaced.
"""

from __future__ import annotations

from typing import Any


class FakeResponse:
    """Minimal requests-like response object for unit tests."""

    def __init__(
        self,
        data: Any = None,
        status_code: int = 200,
        text: str | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.data = data
        self.status_code = status_code
        self.text = text if text is not None else ""
        self.content = content if content is not None else b""
        self.headers = headers or {}

        self.ok = 200 <= self.status_code < 400

    def json(self) -> Any:
        """Return the configured JSON payload."""
        return self.data

    def raise_for_status(self) -> None:
        """Raise an HTTP-style error for unsuccessful responses."""
        if not self.ok:
            raise RuntimeError(
                f"HTTP {self.status_code}: {self.text}"
            )

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None