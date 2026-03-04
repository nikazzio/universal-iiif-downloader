"""Helpers to inspect local and temporary page availability for a document."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from universal_iiif_core.config_manager import get_config_manager


@dataclass(frozen=True)
class PageInventory:
    """Counts of currently available page images."""

    local_pages_count: int
    temp_pages_count: int


def _count_page_images(directory: Path | None) -> int:
    """Count `pag_XXXX.jpg` files in a directory."""
    if directory is None or not directory.exists():
        return 0
    return sum(1 for _ in directory.glob("pag_*.jpg"))


def resolve_page_inventory(*, doc_id: str, scans_dir: Path | None) -> PageInventory:
    """Return local + temporary page counts for a document id."""
    temp_pages_count = 0
    clean_doc_id = str(doc_id or "").strip()
    if clean_doc_id:
        temp_root = Path(get_config_manager().get_temp_dir())
        temp_pages_count = _count_page_images(temp_root / clean_doc_id)
    return PageInventory(
        local_pages_count=_count_page_images(scans_dir),
        temp_pages_count=temp_pages_count,
    )
