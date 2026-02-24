"""Helpers for manuscript classification and catalog metadata enrichment."""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import urlparse

import requests

from .logger import get_logger
from .utils import DEFAULT_HEADERS

logger = get_logger(__name__)

ITEM_TYPES = (
    "manoscritto",
    "libro a stampa",
    "incunabolo",
    "periodico",
    "musica/spartito",
    "mappa/atlante",
    "miscellanea",
    "non classificato",
)

_ITEM_TYPE_ALIASES = {
    "altro": "non classificato",
    "other": "non classificato",
    "unknown": "non classificato",
}

_TYPE_RULES: tuple[tuple[str, tuple[str, ...], float], ...] = (
    ("incunabolo", ("incunab",), 0.96),
    ("musica/spartito", ("spartito", "music", "musica", "chant", "corale"), 0.92),
    ("mappa/atlante", ("atlas", "atlante", "map", "cartograf"), 0.9),
    ("periodico", ("periodic", "journal", "rivista", "gazzetta", "newspaper"), 0.9),
    ("libro a stampa", ("stampa", "printed", "print", "typograph", "edition"), 0.88),
    ("manoscritto", ("manoscr", "manuscript", "codex", "ms "), 0.87),
    ("miscellanea", ("miscellanea", "raccolta", "collectanea"), 0.75),
)


def normalize_item_type(value: str | None) -> str:
    """Normalize legacy/unknown item type values to the canonical taxonomy."""
    text = (value or "").strip().lower()
    if not text:
        return "non classificato"
    text = _ITEM_TYPE_ALIASES.get(text, text)
    if text in ITEM_TYPES:
        return text
    return "non classificato"


def flatten_iiif_value(value: Any) -> str:
    """Flatten common IIIF text containers into a readable string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        chunks = []
        for inner in value.values():
            flattened = flatten_iiif_value(inner)
            if flattened:
                chunks.append(flattened)
        return " | ".join(dict.fromkeys(chunks))
    if isinstance(value, (list, tuple)):
        chunks = []
        for inner in value:
            flattened = flatten_iiif_value(inner)
            if flattened:
                chunks.append(flattened)
        return " | ".join(dict.fromkeys(chunks))
    return str(value).strip()


def metadata_to_map(metadata_obj: Any) -> dict[str, str]:
    """Return normalized metadata map from IIIF metadata list."""
    out: dict[str, str] = {}
    if not isinstance(metadata_obj, list):
        return out
    for entry in metadata_obj:
        if not isinstance(entry, dict):
            continue
        key = flatten_iiif_value(entry.get("label") or entry.get("name") or entry.get("property"))
        val = flatten_iiif_value(entry.get("value") or entry.get("val"))
        if key and val:
            out[key.lower()] = val
    return out


def infer_item_type(
    label: str,
    description: str = "",
    metadata: dict[str, str] | None = None,
) -> tuple[str, float, str]:
    """Infer item type from label/description/metadata tokens."""
    metadata = metadata or {}
    corpus = " ".join(
        chunk
        for chunk in (
            label or "",
            description or "",
            metadata.get("type", ""),
            metadata.get("genre", ""),
            metadata.get("format", ""),
            metadata.get("material", ""),
            metadata.get("description", ""),
        )
        if chunk
    ).lower()
    for item_type, tokens, confidence in _TYPE_RULES:
        for token in tokens:
            if token in corpus:
                return item_type, confidence, f"match:{token}"
    return "non classificato", 0.2, "fallback:no-rule-match"


def extract_see_also_urls(see_also: Any) -> list[str]:
    """Extract normalized URLs from `seeAlso` values in string/dict/list formats."""
    if not see_also:
        return []
    urls: list[str] = []
    items = see_also if isinstance(see_also, list) else [see_also]
    for item in items:
        if isinstance(item, str):
            candidate = item.strip()
        elif isinstance(item, dict):
            candidate = str(item.get("id") or item.get("@id") or item.get("url") or "").strip()
        else:
            candidate = ""
        if candidate:
            urls.append(candidate)
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(urls))


def _compact_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _is_detail_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return "/mss/detail/" in path or "/detail/" in path


def _is_search_url(url: str) -> bool:
    text = (url or "").lower()
    return any(token in text for token in ("advanced-search", "/search", "ricerca", "discover"))


def choose_primary_detail_url(see_also_urls: list[str], shelfmark: str = "", doc_id: str = "") -> str:
    """Choose the most relevant `seeAlso` URL for this manuscript."""
    if not see_also_urls:
        return ""
    tokens = []
    for raw in (shelfmark, doc_id):
        text = (raw or "").strip()
        if not text:
            continue
        tokens.append(_compact_token(text.removeprefix("MSS_").removeprefix("MSS.")))

    detail_urls = [url for url in see_also_urls if _is_detail_url(url)]
    for url in detail_urls:
        compact_url = _compact_token(url)
        if any(token and token in compact_url for token in tokens):
            return url
    if detail_urls:
        return detail_urls[0]

    non_search_urls = [url for url in see_also_urls if not _is_search_url(url)]
    for url in non_search_urls:
        compact_url = _compact_token(url)
        if any(token and token in compact_url for token in tokens):
            return url
    if non_search_urls:
        return non_search_urls[0]

    return see_also_urls[0]


def extract_external_reference(url: str, timeout: int = 8) -> str:
    """Extract a short human reference string from external catalog page."""
    if not url:
        return ""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
    except Exception:
        logger.debug("Reference fetch failed for %s", url, exc_info=True)
        return ""
    return _extract_reference_from_html(response.text)


def _extract_reference_from_html(html: str) -> str:
    candidates: list[str] = []
    for pattern in (
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']title["\'][^>]+content=["\']([^"\']+)["\']',
        r"<h1[^>]*>(.*?)</h1>",
        r"<h2[^>]*>(.*?)</h2>",
        r"<title[^>]*>(.*?)</title>",
    ):
        matches = re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        for raw in matches:
            cleaned = _clean_reference_candidate(raw)
            if cleaned:
                candidates.append(cleaned)

    for candidate in candidates:
        if not _is_generic_site_title(candidate):
            return candidate[:240]

    # If all candidates are generic placeholders (site headers), ignore them.
    return ""


def _clean_reference_candidate(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(re.sub(r"\s+", " ", text)).strip(" -|")
    # Keep the most descriptive chunk from separators commonly used in page titles.
    chunks = [part.strip() for part in re.split(r"\s[\-\|\u2013]\s", text) if part.strip()]
    if len(chunks) > 1:
        # Prefer non-generic chunks first, preserving source order.
        for part in chunks:
            if not _is_generic_site_title(part):
                return part
        # Fallback: choose the longest chunk.
        chunks = sorted(chunks, key=lambda part: (len(part.split()), len(part)), reverse=True)
        text = chunks[0]
    return text


def _is_generic_site_title(text: str) -> bool:
    compact = re.sub(r"[^a-z0-9]+", "", text.lower())
    if compact in {
        "digivatlib",
        "digitalvaticanlibrary",
        "gallica",
        "bnfgallica",
        "oaihandler",
        "oaipmhrepository",
        "oaipmhrepositoryforgallica",
        "repositoryforgallica",
        "bibliothequenationaledefrance",
        "bibliotecaapostolicavaticana",
        "searchanddiscovermanuscripts",
        "searchanddiscovermanuscript",
        "ricercaescoprimanoscritti",
        "advancedsearch",
    }:
        return True
    if "advancedsearch" in compact:
        return True
    if "search" in compact and (
        "manuscript" in compact or "manuscripts" in compact or "manoscritt" in compact or "discover" in compact
    ):
        return True
    return len(text.split()) <= 3 and any(
        token in compact
        for token in (
            "digivatlib",
            "gallica",
            "vatlib",
            "bibliotecaapostolica",
            "oaihandler",
            "searchanddiscovermanuscript",
        )
    )


def is_generic_catalog_text(text: str) -> bool:
    """Public helper to identify site-level placeholder strings."""
    return _is_generic_site_title(text)


def _select_manifest_title(raw_label: str, metadata_map: dict[str, str], shelfmark: str, doc_id: str) -> str:
    """Choose a meaningful title from label/metadata with sane fallbacks."""
    label = (raw_label or "").strip()
    metadata_title = _extract_metadata_title(metadata_map)

    if label and not _is_generic_site_title(label):
        return label
    if metadata_title:
        return metadata_title
    if shelfmark:
        return shelfmark
    if doc_id:
        return doc_id
    return label or "Senza titolo"


def _extract_metadata_title(metadata_map: dict[str, str]) -> str:
    """Extract title-like metadata fields from IIIF metadata map."""
    preferred_keys = ("title", "titre", "titolo", "dc:title", "dc.title")
    for key in preferred_keys:
        value = (metadata_map.get(key) or "").strip()
        if value and not _is_generic_site_title(value):
            return value

    for key, value in metadata_map.items():
        normalized_key = re.sub(r"[^a-z0-9]+", "", key.lower())
        if normalized_key in {"title", "titre", "titolo", "dctitle"}:
            candidate = str(value or "").strip()
            if candidate and not _is_generic_site_title(candidate):
                return candidate
    return ""


def _prefer_reference_title(reference_text: str, label: str, shelfmark: str, doc_id: str) -> bool:
    """Return True when external reference is descriptive enough to be the main title."""
    candidate = (reference_text or "").strip()
    if not candidate or _is_generic_site_title(candidate):
        return False

    compact_candidate = re.sub(r"[^a-z0-9]+", "", candidate.lower())
    for fallback in (label, shelfmark, doc_id):
        compact_fallback = re.sub(r"[^a-z0-9]+", "", str(fallback or "").lower())
        if compact_fallback and compact_candidate == compact_fallback:
            return False
    return True


def parse_manifest_catalog(
    manifest: dict[str, Any],
    manifest_url: str = "",
    doc_id: str = "",
    *,
    enrich_external_reference: bool = False,
) -> dict[str, Any]:
    """Build normalized catalog metadata from a IIIF manifest."""
    raw_label = flatten_iiif_value(manifest.get("label") or manifest.get("title"))
    description = flatten_iiif_value(manifest.get("description"))
    metadata_map = metadata_to_map(manifest.get("metadata") or [])
    shelfmark = (
        metadata_map.get("shelfmark") or metadata_map.get("collocation") or metadata_map.get("segnatura") or doc_id
    )
    label = _select_manifest_title(raw_label, metadata_map, shelfmark, doc_id)
    date_label = metadata_map.get("date") or metadata_map.get("issued") or ""
    language_label = metadata_map.get("language") or ""
    attribution = flatten_iiif_value(manifest.get("attribution") or manifest.get("requiredStatement"))
    see_also_urls = extract_see_also_urls(manifest.get("seeAlso"))
    source_detail_url = choose_primary_detail_url(see_also_urls, shelfmark, doc_id)
    reference_text = ""
    if enrich_external_reference and source_detail_url and _is_detail_url(source_detail_url):
        reference_text = extract_external_reference(source_detail_url)
    if reference_text and _is_generic_site_title(reference_text):
        reference_text = ""
    if not reference_text and source_detail_url and _is_detail_url(source_detail_url):
        parsed = urlparse(source_detail_url)
        if parsed.path:
            reference_text = parsed.path.rstrip("/").split("/")[-1].replace(".", " ")
            reference_text = reference_text.strip()

    item_type, item_type_confidence, item_type_reason = infer_item_type(label, description, metadata_map)
    catalog_title = reference_text if _prefer_reference_title(reference_text, label, shelfmark, doc_id) else label
    manifest_id = str(manifest.get("@id") or manifest.get("id") or manifest_url or "").strip()

    return {
        "manifest_id": manifest_id,
        "label": label,
        "description": description,
        "attribution": attribution,
        "shelfmark": shelfmark,
        "date_label": date_label,
        "language_label": language_label,
        "see_also_urls": see_also_urls,
        "source_detail_url": source_detail_url,
        "reference_text": reference_text,
        "catalog_title": catalog_title,
        "item_type": item_type,
        "item_type_confidence": item_type_confidence,
        "item_type_reason": item_type_reason,
        "metadata_map": metadata_map,
        "metadata_json": json.dumps(metadata_map, ensure_ascii=False),
    }
