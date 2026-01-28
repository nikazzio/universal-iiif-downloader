"""Mirador configuration helpers used across the FastHTML UI."""

from __future__ import annotations

import json

from studio_ui.config import get_setting

_BASE_CONFIG = {
    "thumbnailNavigationPosition": "far-bottom",
    "allowClose": False,
    "allowMaximize": False,
    "defaultSideBarPanel": "info",
    "sideBarOpenAtStartup": False,
    "views": [{"key": "single"}],
}

_OPEN_SEADRAGON_DEFAULTS = {
    "maxZoomPixelRatio": 5,
    "maxZoomLevel": 25,
    "minZoomLevel": 0.35,
}


def build_window_config(manifest_url: str, canvas_id: str | None = None) -> dict:
    """Return the merged Mirador window configuration."""
    mirador_settings = get_setting("viewer.mirador", {}) or {}

    window_config = {"manifestId": manifest_url, **_BASE_CONFIG}
    window_config.update({k: v for k, v in mirador_settings.items() if k != "openSeadragonOptions"})
    window_config["openSeadragonOptions"] = {
        **_OPEN_SEADRAGON_DEFAULTS,
        **mirador_settings.get("openSeadragonOptions", {}),
    }
    if canvas_id:
        window_config["canvasId"] = canvas_id
    return window_config


def window_config_json(manifest_url: str, canvas_id: str | None = None) -> str:
    """Serialize the Mirador configuration with predictable casing."""
    return json.dumps(build_window_config(manifest_url, canvas_id))
