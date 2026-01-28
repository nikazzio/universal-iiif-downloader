"""CLI package for Universal IIIF Downloader."""

from __future__ import annotations

from .cli import main, resolve_url, wizard_mode  # noqa: F401

__all__ = ["main", "resolve_url", "wizard_mode"]
