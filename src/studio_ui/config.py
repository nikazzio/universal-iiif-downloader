"""FastHTML UI configuration helpers.

This module centralizes access to runtime configuration values that the
FastHTML frontend depends on. The UI should call the functions exposed
here instead of importing the core config manager directly, keeping the
core runtime configuration concerns separate from presentation logic.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from universal_iiif_core.config_manager import get_config_manager


@lru_cache(maxsize=1)
def _manager():
    """Return the shared config manager instance for UI usage."""
    return get_config_manager()


def get_setting(path: str, default: Any = None) -> Any:
    """Read configuration values under the settings namespace."""
    return _manager().get_setting(path, default)


def get_api_key(provider: str, default: str = "") -> str:
    """Read API keys in a UI-friendly manner."""
    return _manager().get_api_key(provider, default)


def get_downloads_dir():
    """Directory containing downloaded IIIF assets for the UI."""
    return _manager().get_downloads_dir()


def get_temp_dir():
    """Directory used for temporary image processing."""
    return _manager().get_temp_dir()


def get_models_dir():
    """Directory holding OCR/HTR models."""
    return _manager().get_models_dir()


def get_logs_dir():
    """Directory for application logs."""
    return _manager().get_logs_dir()


def get_snippets_dir():
    """Directory dedicated to snippet thumbnails and crops."""
    return _manager().get_snippets_dir()
