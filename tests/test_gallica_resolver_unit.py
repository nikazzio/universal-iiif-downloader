from universal_iiif_core.resolvers.gallica import GallicaResolver


def test_gallica_resolver_short_id():
    """Test Gallica Resolver with short ID input."""
    r = GallicaResolver()
    short = "bpt6k9761787t"
    assert r.can_resolve(short)
    manifest, doc_id = r.get_manifest_url(short)
    assert manifest.endswith(f"/iiif/ark:/12148/{short}/manifest.json")
    assert doc_id == short


def test_gallica_resolver_full_ark():
    """Test Gallica Resolver with full ARK URL."""
    r = GallicaResolver()
    url = "https://gallica.bnf.fr/ark:/12148/btv1b84260335"
    assert r.can_resolve(url)
    manifest, doc_id = r.get_manifest_url(url)
    assert manifest.endswith("/iiif/ark:/12148/btv1b84260335/manifest.json")
    assert doc_id == "btv1b84260335"


def test_gallica_resolver_normalization():
    """Test Gallica Resolver normalizes URLs to the canonical IIIF format."""
    r = GallicaResolver()
    # Input: URL "vecchio stile" o incompleto (senza /iiif/)
    input_url = "https://gallica.bnf.fr/ark:/12148/btv1b84260335/manifest.json"

    # Output atteso: URL canonico con /iiif/
    expected_url = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b84260335/manifest.json"

    manifest, doc_id = r.get_manifest_url(input_url)

    assert manifest == expected_url
    assert doc_id == "btv1b84260335"
