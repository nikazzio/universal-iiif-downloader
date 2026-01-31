"""Test script for library search APIs (Gallica SRU and Oxford).

Note: Oxford API is deprecated as of Jan 2026 and will return errors.
Run from project root: python -m tests.test_search_apis
"""

import pytest
import requests
from requests import RequestException

from universal_iiif_core.config_manager import get_config_manager

pytestmark = pytest.mark.skipif(
    not bool(get_config_manager().get_setting("testing.run_live_tests", False)),
    reason="Live tests require network access; set settings.testing.run_live_tests=true in config.json to enable.",
)


def test_gallica():
    """Smoke-test Gallica SRU search endpoint."""
    query = "dante"
    print(f"Testing Gallica with query: {query}")
    url = "https://gallica.bnf.fr/SRU"
    params = {
        "operation": "searchRetrieve",
        "version": "1.2",
        "query": f'dc.title all "{query}" and dc.type all "manuscrit"',
        "maximumRecords": "5",
        "responseFormat": "json",  # Testing if this works
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")
        if "json" in r.headers.get("Content-Type", "").lower():
            print("Successfully got JSON!")
            print(r.json().get("searchRetrieveResponse", {}).get("records", [])[:1])
        else:
            print("Returned XML instead of JSON.")
    except (RequestException, ValueError) as e:
        print(f"Error: {e}")


def test_oxford():
    """Oxford search API has been deprecated — ensure our stub behaves."""
    from universal_iiif_core.resolvers.discovery import search_oxford

    results = search_oxford("dante")
    assert results == []


if __name__ == "__main__":
    test_gallica()
    test_oxford()
