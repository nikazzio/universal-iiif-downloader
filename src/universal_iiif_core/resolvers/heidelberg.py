from __future__ import annotations

import re

from .base import BaseResolver

_ID_RE = re.compile(r"\b([a-z]{2,6}\d{2,})\b", flags=re.IGNORECASE)


class HeidelbergResolver(BaseResolver):
    """Resolver for Universitaetsbibliothek Heidelberg manifests."""

    manifest_root = "https://digi.ub.uni-heidelberg.de/diglit/iiif"

    def can_resolve(self, url_or_id: str) -> bool:
        """Return True for supported Heidelberg URLs or catalog IDs."""
        text = (url_or_id or "").strip()
        if not text:
            return False
        return "digi.ub.uni-heidelberg.de" in text.lower() or bool(_ID_RE.search(text))

    def get_manifest_url(self, url_or_id: str) -> tuple[str | None, str | None]:
        """Build the canonical Heidelberg manifest URL."""
        text = (url_or_id or "").strip()
        if not text:
            return None, None

        doc_id = self._extract_id(text)
        if not doc_id:
            return None, None

        return f"{self.manifest_root}/{doc_id}/manifest.json", doc_id

    @staticmethod
    def _extract_id(value: str) -> str | None:
        if match := _ID_RE.search(value):
            return match.group(1).lower()
        return None
