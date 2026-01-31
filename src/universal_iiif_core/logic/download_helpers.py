from __future__ import annotations

import re


def sanitize_filename(label: str) -> str:
    """Return a filesystem-safe identifier derived from `label`."""
    safe = "".join([c for c in str(label) if c.isalnum() or c in (" ", ".", "_", "-")])
    return safe.strip().replace(" ", "_")


def derive_identifier(
    manifest_url: str, output_folder_name: str | None, library: str | None, label: str | None
) -> str:
    """Derive a compact folder identifier for a manuscript.

    Priority:
    1. cleaned `output_folder_name` without leading library
    2. ARK token found in `manifest_url`
    3. UUID-like token in `manifest_url`
    4. sanitized `label`
    5. last meaningful URL path segment
    """
    lib = (library or "").strip()
    if output_folder_name:
        pattern = r"^\s*" + re.escape(lib) + r"\s*[-–:]*\s*"
        candidate = re.sub(pattern, "", output_folder_name, flags=re.IGNORECASE).strip()
        if candidate:
            return sanitize_filename(candidate)

    m = re.search(r"ark[:/]+(?P<ark>[^/]+)", manifest_url)
    if m:
        return sanitize_filename(m.group("ark"))

    m = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", manifest_url)
    if m:
        return sanitize_filename(m.group(0))

    if label:
        return sanitize_filename(label)

    parts = [p for p in manifest_url.split("/") if p]
    if parts:
        last = parts[-2] if parts[-1].lower().endswith("manifest.json") and len(parts) >= 2 else parts[-1]
        return sanitize_filename(last)

    return "unknown_manuscript"
