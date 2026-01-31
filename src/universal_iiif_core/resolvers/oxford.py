import re

from .base import BaseResolver


class OxfordResolver(BaseResolver):
    """Resolver for Digital Bodleian (Oxford) UUID-based manifests."""

    def can_resolve(self, url_or_id: str) -> bool:
        """Check if the input can be resolved by this resolver."""
        s = url_or_id or ""
        if "digital.bodleian.ox.ac.uk" in s:
            return True
        # Also accept bare UUIDs
        uuid_re = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
        return bool(uuid_re.search(s))

    def get_manifest_url(self, url_or_id: str) -> tuple[str | None, str | None]:
        """Return the IIIF manifest URL and document ID for a given Oxford shelfmark or URL."""
        s = url_or_id or ""
        uuid_re = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I)
        m = uuid_re.search(s)
        if not m:
            return None, None
        uuid = m.group(1).lower()
        manifest_url = f"https://iiif.bodleian.ox.ac.uk/iiif/manifest/{uuid}.json"
        return manifest_url, uuid
