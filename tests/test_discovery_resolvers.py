"""Unit tests for resolver helpers (no network requests).

Focus on normalisation and resolver URL building for Vaticana, Gallica and Oxford.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from universal_iiif_core.resolvers.discovery import resolve_shelfmark
from universal_iiif_core.resolvers.gallica import GallicaResolver
from universal_iiif_core.resolvers.oxford import OxfordResolver
from universal_iiif_core.resolvers.vatican import normalize_shelfmark


def test_normalize_vatican_variants():
    """Test Vatican shelfmark normalization with different formats."""
    assert normalize_shelfmark("Urb. lat. 123") == "MSS_Urb.lat.123"
    assert normalize_shelfmark("urb lat 123") == "MSS_Urb.lat.123"
    assert normalize_shelfmark("Vat.Lat.123") == "MSS_Vat.lat.123"


def test_resolve_shelfmark_vatican():
    """Test Vatican Resolver with normalized shelfmark."""
    url, doc_id = resolve_shelfmark("Vaticana", "Urb. lat. 123")
    assert url is not None and url.endswith("MSS_Urb.lat.123/manifest.json")
    assert doc_id == "MSS_Urb.lat.123"


def test_gallica_resolver_short_and_ark():
    """Test Gallica Resolver with short ID and full ARK URL."""
    r = GallicaResolver()
    manifest, doc = r.get_manifest_url("btv1b84260335")
    assert manifest == "https://gallica.bnf.fr/iiif/ark:/12148/btv1b84260335/manifest.json"
    assert doc == "btv1b84260335"

    full, doc2 = r.get_manifest_url("https://gallica.bnf.fr/ark:/12148/btv1b84260335")
    assert full == "https://gallica.bnf.fr/iiif/ark:/12148/btv1b84260335/manifest.json"
    assert doc2 == "btv1b84260335"


def test_oxford_uuid_case_insensitive():
    """Test Oxford Resolver with UUID in different cases."""
    r = OxfordResolver()
    upper = "080F88F5-7586-4B8A-8064-63AB3495393C"
    manifest, uid = r.get_manifest_url(upper)
    assert uid == "080f88f5-7586-4b8a-8064-63ab3495393c"
    assert manifest.endswith(f"{uid}.json")
