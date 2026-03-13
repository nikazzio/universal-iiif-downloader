from __future__ import annotations

import re
from urllib.parse import urlparse

from .base import BaseResolver

_DETAILS_RE = re.compile(r"/details/(?P<identifier>[^/?#]+)", flags=re.IGNORECASE)
_HELPER_RE = re.compile(r"/iiif/helper/(?P<identifier>[^/?#]+)", flags=re.IGNORECASE)
_MANIFEST_RE = re.compile(r"/iiif/(?P<identifier>[^/?#]+)/manifest\.json$", flags=re.IGNORECASE)


class ArchiveOrgResolver(BaseResolver):
    """Resolver for Internet Archive IIIF manifests."""

    manifest_root = "https://iiif.archive.org/iiif"

    def can_resolve(self, url_or_id: str) -> bool:
        """Return True for supported Archive.org item or IIIF URLs."""
        text = (url_or_id or "").strip()
        if not text:
            return False
        lowered = text.lower()
        return "archive.org/" in lowered or "iiif.archive.org/" in lowered

    def get_manifest_url(self, url_or_id: str) -> tuple[str | None, str | None]:
        """Build the canonical Archive.org IIIF manifest URL."""
        text = (url_or_id or "").strip()
        if not text:
            return None, None

        identifier = self._extract_identifier(text)
        if not identifier:
            return None, None

        return f"{self.manifest_root}/{identifier}/manifest.json", identifier

    @staticmethod
    def _extract_identifier(value: str) -> str | None:
        direct = value.strip().strip("/")
        if direct and "://" not in direct and "/" not in direct and " " not in direct:
            return direct

        parsed = urlparse(value)
        path = parsed.path or ""
        if manifest_match := _MANIFEST_RE.search(path):
            return manifest_match.group("identifier")
        if details_match := _DETAILS_RE.search(path):
            return details_match.group("identifier")
        if helper_match := _HELPER_RE.search(path):
            return helper_match.group("identifier")
        return None
