"""Studio workspace page layouts."""

import json

from fasthtml.common import H2, A, Div, Script, Span

from studio_ui.components.studio.tabs import render_studio_tabs
from studio_ui.components.viewer import mirador_viewer
from studio_ui.ocr_state import is_ocr_job_running


def studio_layout(
    title,
    library,
    doc_id,
    page,
    manifest_url,
    initial_canvas,
    manifest_json,
    total_pages,
    meta,
    export_fragment=None,
    export_url: str | None = None,
    asset_status: str = "",
    has_native_pdf: bool | None = None,
    pdf_local_available: bool = False,
    local_pages_count: int = 0,
    temp_pages_count: int = 0,
    manifest_total_pages: int = 0,
    mirador_enabled: bool = True,
    mirador_override_url: str = "",
):
    """Render the main Studio split-view layout."""
    status_value = (asset_status or "unknown").strip().lower()
    status_chip_map = {
        "complete": "app-chip app-chip-success",
        "downloading": "app-chip app-chip-primary",
        "running": "app-chip app-chip-primary",
        "queued": "app-chip app-chip-accent",
        "partial": "app-chip app-chip-warning",
        "error": "app-chip app-chip-danger",
        "saved": "app-chip app-chip-neutral",
    }
    status_chip_cls = status_chip_map.get(status_value, "app-chip app-chip-neutral")
    pdf_source_cls = "app-chip app-chip-success" if has_native_pdf else "app-chip app-chip-neutral"
    pdf_local_cls = "app-chip app-chip-primary" if pdf_local_available else "app-chip app-chip-neutral"
    temp_chip_cls = "app-chip app-chip-warning" if int(temp_pages_count or 0) > 0 else "app-chip app-chip-neutral"
    local_progress = (
        f"{int(local_pages_count)}/{int(manifest_total_pages)}"
        if int(manifest_total_pages or 0) > 0
        else str(int(local_pages_count or 0))
    )
    if mirador_enabled:
        viewer_block = Div(
            *mirador_viewer(manifest_url, "mirador-viewer", canvas_id=initial_canvas),
            cls="flex-none bg-slate-900 border-r border-slate-200 dark:border-slate-700",
            style="width: 55%;",
        )
    else:
        viewer_block = Div(
            Div(
                Span(
                    "Viewer bloccato finche non sono disponibili tutte le immagini locali.",
                    cls="text-sm font-semibold",
                ),
                Span(
                    f"Pagine locali: {local_progress} • Temporanee: {int(temp_pages_count or 0)}",
                    cls="text-xs text-slate-300",
                ),
                (
                    Span(
                        "Apri comunque Mirador (puo mostrare anteprime remote non ancora locali).",
                        cls="text-xs text-slate-400",
                    )
                    if mirador_override_url
                    else ""
                ),
                (
                    A(
                        "Apri Mirador comunque",
                        href=mirador_override_url,
                        cls="app-btn app-btn-warning text-xs",
                    )
                    if mirador_override_url
                    else ""
                ),
                cls="flex flex-col gap-3 p-5 max-w-md",
            ),
            cls=(
                "flex-none bg-slate-900 border-r border-slate-200 dark:border-slate-700 "
                "text-slate-100 flex items-center justify-center"
            ),
            style="width: 55%;",
            **{"data-mirador-gated": "1"},
        )

    return Div(
        Div(
            # LEFT: Mirador (55%)
            viewer_block,
            # RIGHT: Editor (45%)
            Div(
                Div(
                    Div(
                        Div(
                            Div(
                                H2(title, cls="text-3xl font-black text-slate-900 dark:text-white tracking-tight"),
                                Div(
                                    Span(
                                        library,
                                        cls="app-chip app-chip-primary text-[11px] font-bold uppercase tracking-wider",
                                    ),
                                    Span(
                                        (asset_status or "unknown").upper(),
                                        cls=f"{status_chip_cls} text-[10px] font-bold",
                                    ),
                                    Span(
                                        "PDF nativo" if has_native_pdf else "Solo immagini",
                                        cls=(
                                            f"{pdf_source_cls} text-[10px] font-bold"
                                            if has_native_pdf is not None
                                            else "app-chip app-chip-neutral text-[10px] font-bold"
                                        ),
                                    ),
                                    Span(
                                        "PDF locale ✓" if pdf_local_available else "PDF locale -",
                                        cls=f"{pdf_local_cls} text-[10px] font-bold",
                                    ),
                                    Span(
                                        f"Locali {local_progress}",
                                        cls="app-chip app-chip-neutral text-[10px] font-bold",
                                    ),
                                    Span(
                                        f"Temp {int(temp_pages_count or 0)}",
                                        cls=f"{temp_chip_cls} text-[10px] font-bold",
                                    ),
                                    Span(
                                        doc_id,
                                        cls="app-chip app-chip-neutral text-[9px] font-mono",
                                    ),
                                    cls="flex gap-2 mt-1",
                                ),
                                cls="flex-1 min-w-0",
                            ),
                            cls="flex items-start justify-between",
                        ),
                        cls="px-6 py-8 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50",
                    ),
                    # HTMX Target for Tab Content
                    Div(
                        render_studio_tabs(
                            doc_id,
                            library,
                            int(page),
                            meta,
                            total_pages,
                            manifest_json=manifest_json,
                            is_ocr_loading=is_ocr_job_running(doc_id, int(page)),
                            export_fragment=export_fragment,
                            export_url=export_url,
                        ),
                        id="studio-right-panel",
                        cls="flex-1 overflow-hidden h-full",
                    ),
                    cls="h-full flex flex-col",
                ),
                cls="flex-none bg-white dark:bg-slate-900 shadow-2xl z-10",
                style="width: 45%;",
            ),
            cls="flex h-screen",
        ),
        # Modal placeholder
        Div(id="cropper-modal-container"),
        Script(f"""
            (function() {{
                if (window.__studioMiradorListenerBound) return;
                window.__studioMiradorListenerBound = true;

                document.addEventListener('mirador:page-changed', function(e) {{
                    const panel = document.getElementById('studio-right-panel');
                    if (!panel) return;

                    const newPage = e.detail.page;
                    const library = {json.dumps(library)};
                    const docId = {json.dumps(doc_id)};
                    const totalPages = {total_pages};

                    console.log('📄 Page changed to:', newPage);

                    // 1. Update URL History
                    const url = new URL(window.location);
                    url.searchParams.set('page', newPage);
                    window.history.pushState({{}}, '', url);

                    const target = '/studio/partial/tabs?doc_id=' + encodeURIComponent(docId) +
                        '&library=' + encodeURIComponent(library) +
                        '&page=' + newPage;
                    htmx.ajax('GET', target, {{
                        target: '#studio-right-panel',
                        swap: 'innerHTML'
                    }});
                }});
            }})();
        """),
        cls="flex flex-col h-screen overflow-hidden",
    )
