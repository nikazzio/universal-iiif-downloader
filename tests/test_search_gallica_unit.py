from pathlib import Path

from universal_iiif_core.resolvers.discovery import search_gallica


def test_search_gallica_parsing(monkeypatch):
    """Parse a saved SRU XML response and ensure we extract ARK and title."""
    fixture = Path(__file__).parent / "fixtures" / "gallica_sample.xml"
    content = fixture.read_bytes()

    class DummyResp:
        def __init__(self, content_bytes: bytes):
            self.content = content_bytes
            self.status_code = 200
            self.headers = {"Content-Type": "application/xml"}

        def raise_for_status(self):
            return None

    def fake_get(url, params=None, headers=None, timeout=None):
        return DummyResp(content)

    monkeypatch.setattr("universal_iiif_core.resolvers.discovery.requests.get", fake_get)

    results = search_gallica("dante", max_records=5)
    assert results, "Expected at least one result from fixture"
    first = results[0]
    assert first["id"] == "btv1b10033406t"
    assert "Dante" in first["title"] or "Dante" in first["title"].capitalize()
