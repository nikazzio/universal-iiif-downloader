"""Live tests for Vatican, Gallica, and Oxford.

Uses real network requests. Skips automatically if configured in config.json.
"""

from pathlib import Path

import pytest

from universal_iiif_core.config_manager import get_config_manager
from universal_iiif_core.logic import IIIFDownloader
from universal_iiif_core.resolvers.discovery import resolve_shelfmark

# Skip all tests in this file if live testing is disabled
pytestmark = pytest.mark.skipif(
    not bool(get_config_manager().get_setting("testing.run_live_tests", False)),
    reason="Live tests disabled in config.json",
)


def test_vatican_live_flow(tmp_path: Path):
    """Test Vatican Resolver + Partial Download (Headers Check)."""
    print("\n[Test] Vatican Live...")

    # 1. Resolve
    shelfmark = "Urb.lat.1779"
    manifest_url, doc_id = resolve_shelfmark("Vaticana", shelfmark)

    # Type Guard: Assicura al linter che non è None
    assert manifest_url is not None, "Resolver returned None for Vatican"
    assert manifest_url == "https://digi.vatlib.it/iiif/MSS_Urb.lat.1779/manifest.json"
    assert doc_id == "MSS_Urb.lat.1779"

    # 2. Init Downloader (Download Manifest)
    # Usiamo tmp_path così i file vengono cancellati alla fine del test
    d = IIIFDownloader(manifest_url, output_dir=str(tmp_path), output_name="test_vat.pdf", library="Vaticana")

    assert "Urb.lat.1779" in d.label
    assert len(d.get_canvases()) > 10


def test_gallica_live_flow(tmp_path: Path):
    """Test Gallica Resolver + Manifest Fetch."""
    print("\n[Test] Gallica Live...")

    # Usa un ID stabile
    input_id = "bpt6k9604118j"
    manifest_url, doc_id = resolve_shelfmark("Gallica", input_id)

    # Type Guard
    assert manifest_url is not None, "Resolver returned None for Gallica"

    expected_url = f"https://gallica.bnf.fr/iiif/ark:/12148/{input_id}/manifest.json"
    assert manifest_url == expected_url
    assert doc_id == input_id

    # Prova a scaricare il manifest
    d = IIIFDownloader(manifest_url, output_dir=str(tmp_path), library="Gallica")
    # Se il manifest è scaricato, label deve essere popolato
    assert d.label != "unknown_manuscript"


def test_oxford_live_flow(tmp_path: Path):
    """Test Oxford Resolver + Manifest Fetch."""
    print("\n[Test] Oxford Live...")

    uuid = "080f88f5-7586-4b8a-8064-63ab3495393c"
    manifest_url, doc_id = resolve_shelfmark("Oxford", uuid)

    # Type Guard
    assert manifest_url is not None, "Resolver returned None for Oxford"

    assert doc_id == uuid
    assert "iiif.bodleian.ox.ac.uk" in manifest_url

    d = IIIFDownloader(manifest_url, output_dir=str(tmp_path), library="Oxford")
    # Verifica che abbia letto i canvas
    assert len(d.get_canvases()) > 0
