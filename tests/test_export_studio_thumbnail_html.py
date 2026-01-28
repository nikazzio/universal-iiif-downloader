import json

from studio_ui.common.mirador import window_config_json


def test_window_config_includes_manifest_url():
    """Mirador helper should embed the manifest URL in the config."""
    manifest_url = "https://example.org/iiif/manifest.json"
    cfg = json.loads(window_config_json(manifest_url))

    assert cfg["manifestId"] == manifest_url
