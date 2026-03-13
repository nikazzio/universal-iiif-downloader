from __future__ import annotations

import re

from .base import BaseResolver

_DIRECT_CAMBRIDGE_ID_RE = re.compile(r"(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+){2,}")
_URL_CAMBRIDGE_ID_RE = re.compile(r"([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)")


class CambridgeResolver(BaseResolver):
    """Resolver for Cambridge University Digital Library manifests."""

    base_url = "https://cudl.lib.cam.ac.uk/iiif"

    def can_resolve(self, url_or_id: str) -> bool:
        """Return True for supported CUDL URLs or direct shelfmark-style IDs."""
        text = (url_or_id or "").strip()
        if not text:
            return False
        return "cudl.lib.cam.ac.uk" in text.lower() or bool(_DIRECT_CAMBRIDGE_ID_RE.fullmatch(text))

    def get_manifest_url(self, url_or_id: str) -> tuple[str | None, str | None]:
        """Build the canonical CUDL manifest URL from a URL or direct identifier."""
        text = (url_or_id or "").strip()
        if not text:
            return None, None

        doc_id = self._extract_id(text)
        if not doc_id:
            return None, None

        return f"{self.base_url}/{doc_id}", doc_id

    @staticmethod
    def _extract_id(value: str) -> str | None:
        if "cudl.lib.cam.ac.uk" not in value.lower():
            candidate = value.strip()
            return candidate if _DIRECT_CAMBRIDGE_ID_RE.fullmatch(candidate) else None

        trimmed = value.split("?", 1)[0].split("#", 1)[0].rstrip("/")
        parts = [part for part in trimmed.split("/") if part]
        if not parts:
            return None

        candidate = parts[-1]
        match = _URL_CAMBRIDGE_ID_RE.fullmatch(candidate)
        return match.group(1) if match else None
