"""Helpers for FastHTML + HTMX interactions."""

from urllib.parse import quote

from fasthtml.common import Script


def history_refresh_script(doc_id: str, library: str, page_idx: int, info_message: str | None = None) -> Script:
    """Return a script that triggers a history panel refresh with HTMX."""
    encoded_doc = quote(doc_id, safe="")
    encoded_lib = quote(library, safe="")
    hx_url = f"/studio/partial/history?doc_id={encoded_doc}&library={encoded_lib}&page={page_idx}"
    if info_message:
        hx_url += f"&info_message={quote(info_message, safe='')}"

    parts = [
        "(function(){",
        "setTimeout(function(){ try{ htmx.ajax('GET', '",
        hx_url,
        "', {target: '#tab-content-history', ",
        "swap: 'innerHTML'}); }catch(e){console.error('history refresh failed', e);} }, 20);",
        "})();",
    ]
    return Script("".join(parts))
