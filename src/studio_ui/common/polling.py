"""Shared polling helpers for HTMX fragments."""

from __future__ import annotations

from studio_ui.config import get_setting

_MIN_SECONDS = 1
_MAX_SECONDS = 30
_DEFAULT_DOWNLOAD_MANAGER_SECONDS = 3
_DEFAULT_DOWNLOAD_STATUS_SECONDS = 3


def _safe_interval(value: object, *, default: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return max(_MIN_SECONDS, min(_MAX_SECONDS, parsed))


def get_download_manager_interval_seconds() -> int:
    """Read poll interval for the Download Manager fragment."""
    configured = get_setting("ui.polling.download_manager_interval_seconds", _DEFAULT_DOWNLOAD_MANAGER_SECONDS)
    return _safe_interval(configured, default=_DEFAULT_DOWNLOAD_MANAGER_SECONDS)


def get_download_status_interval_seconds() -> int:
    """Read poll interval for the single download status card."""
    configured = get_setting("ui.polling.download_status_interval_seconds", _DEFAULT_DOWNLOAD_STATUS_SECONDS)
    return _safe_interval(configured, default=_DEFAULT_DOWNLOAD_STATUS_SECONDS)


def build_every_seconds_trigger(seconds: int) -> str:
    """Build a canonical HTMX polling trigger string."""
    bounded = max(_MIN_SECONDS, min(_MAX_SECONDS, int(seconds)))
    return f"every {bounded}s"
