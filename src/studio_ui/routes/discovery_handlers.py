"""Route handlers for the Discovery page.

Handlers are top-level functions so `setup_discovery_routes` can remain
very small and satisfy ruff's complexity check.
"""

from typing import Any
from urllib.parse import unquote

from fasthtml.common import Button, Div, P, Request, Span

from studio_ui.components.layout import base_layout
from studio_ui.config import get_setting
from studio_ui.routes.discovery_helpers import analyze_manifest, start_downloader_thread
from studio_ui.routes.discovery_render import discovery_content, render_download_status, render_preview
from universal_iiif_core.logger import get_logger
from universal_iiif_core.resolvers.discovery import resolve_shelfmark

logger = get_logger(__name__)

# Shared progress store used by the polling endpoint
download_progress: dict[str, Any] = {}


def discovery_page(request: Request):
    """Render the Discovery page.

    Returns just the content for HTMX requests, otherwise uses the
    application's base layout.
    """
    content = discovery_content()
    if request.headers.get("HX-Request") == "true":
        return content
    return base_layout("Discovery & Download", content, active_page="discovery")


def resolve_manifest(library: str, shelfmark: str):
    """Resolve a shelfmark or URL and return a preview fragment."""
    try:
        logger.info(f"🔍 Resolving: {library} / {shelfmark}")
        manifest_url, doc_id_hint = resolve_shelfmark(library, shelfmark)

        if not manifest_url:
            return Div(
                Span("⚠️", cls="text-xl mr-2"),
                Span(doc_id_hint or "ID non risolvibile", cls="font-medium"),
                cls=(
                    "bg-yellow-100 dark:bg-yellow-900 border border-yellow-400 "
                    "dark:border-yellow-600 text-yellow-700 dark:text-yellow-200 "
                    "px-4 py-3 rounded mt-4"
                ),
            )

        manifest_info = analyze_manifest(manifest_url)

        preview_data = {
            "url": manifest_url,
            "id": doc_id_hint,
            "label": manifest_info["label"],
            "library": library,
            "description": manifest_info["description"][:500],
            "pages": manifest_info["pages"],
        }

        return render_preview(preview_data)

    except Exception as exc:
        logger.exception("❌ Resolution error: %s", exc)
        return Div(
            Span("❌", cls="text-xl mr-2"),
            Span(f"Errore: {str(exc)}", cls="font-medium"),
            cls=(
                "bg-red-100 dark:bg-red-900 border border-red-400 "
                "dark:border-red-600 text-red-700 dark:text-red-200 "
                "px-4 py-3 rounded mt-4"
            ),
        )


def start_download(manifest_url: str, doc_id: str, library: str):
    """Start an asynchronous download job and return a polling fragment."""
    try:
        manifest_url = unquote(manifest_url)
        doc_id = unquote(doc_id)
        library = unquote(library)

        logger.info(f"🚀 Starting download: {doc_id} from {library}")

        download_id = start_downloader_thread(
            manifest_url=manifest_url,
            doc_id=doc_id,
            library=library,
            progress_store=download_progress,
            workers=int(get_setting("system.download_workers", 4)),
        )

        return render_download_status(download_id, doc_id)

    except Exception as exc:
        logger.exception("❌ Start download error: %s", exc)
        return Div(f"Errore: {str(exc)}", cls="text-red-600")


def get_download_status(download_id: str):
    """Return current download status for polling (HTMX endpoint)."""
    status_data = download_progress.get(download_id, {"status": "unknown"})

    if status_data["status"] == "complete":
        return Div(
            Div(
                Span("🎉", cls="text-2xl mr-2"),
                Span("Download Completato!", cls="font-bold"),
                cls=("flex items-center text-green-600 dark:text-green-400 mb-2"),
            ),
            P(f"Il documento '{download_id.split('_')[-1]}' è pronto nello Studio."),
            Button(
                "Vai allo Studio →",
                hx_get=(f"/studio?library={download_id.split('_')[0]}&doc_id={download_id.split('_')[-1]}"),
                hx_target="#app-main",
                hx_swap="innerHTML",
                hx_push_url="true",
                cls=("bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded mt-4 transition"),
            ),
            cls=("bg-green-100 dark:bg-green-900/30 p-4 rounded border border-green-400"),
        )

    if "error" in status_data["status"]:
        return Div(
            Span("❌", cls="text-2xl mr-2"),
            Span(
                f"Errore Download: {status_data['status'].replace('error: ', '')}",
                cls="font-bold text-red-600",
            ),
            cls=("bg-red-100 dark:bg-red-900/30 p-4 rounded border border-red-400"),
        )

    curr = status_data.get("current", 0)
    total = status_data.get("total", 0)
    percent = int((curr / total * 100) if total > 0 else 0)

    return Div(
        Div(
            Span("⏳", cls="animate-spin-slow text-xl mr-2"),
            Span(
                f"Scaricamento in corso: {curr}/{total}",
                cls=("font-medium text-indigo-600 dark:text-indigo-400"),
            ),
            cls="flex items-center mb-2",
        ),
        Div(
            Div(
                style=f"width: {percent}%",
                cls="h-full bg-indigo-600 transition-all duration-300",
            ),
            cls=("w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"),
        ),
        hx_get=f"/api/download_status/{download_id}",
        hx_trigger="every 1.5s",
        hx_swap="outerHTML",
    )
