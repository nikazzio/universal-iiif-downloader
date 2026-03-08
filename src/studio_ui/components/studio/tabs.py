"""Studio Tabs Manager Component."""

import json
from urllib.parse import quote

from fasthtml.common import Button, Div, Script, Span

from studio_ui.components.studio.history import history_tab_content
from studio_ui.components.studio.info import info_tab_content, visual_tab_content
from studio_ui.components.studio.snippets import snippets_tab_content
from studio_ui.components.studio.transcription import transcription_tab_content


def render_studio_tabs(
    doc_id,
    library,
    page,
    meta,
    total_pages,
    manifest_json=None,
    *,
    is_ocr_loading: bool = False,
    ocr_error: str | None = None,
    history_message: str | None = None,
    export_fragment=None,
    export_url: str | None = None,
    active_tab: str = "transcription",
):
    """Render the studio tabs."""
    page_idx = int(page)
    allowed_tabs = {"transcription", "snippets", "history", "visual", "info", "images", "output", "jobs"}
    safe_active_tab = str(active_tab or "transcription").strip().lower()
    if safe_active_tab == "export":
        safe_active_tab = "images"
    if safe_active_tab not in allowed_tabs:
        safe_active_tab = "transcription"
    encoded_doc = quote(str(doc_id), safe="")
    encoded_lib = quote(str(library), safe="")
    export_urls = {
        "images": (
            f"/studio/partial/export?doc_id={encoded_doc}&library={encoded_lib}&page={page_idx}&tab=images&subtab=pages"
        ),
        "output": (
            f"/studio/partial/export?doc_id={encoded_doc}&library={encoded_lib}&page={page_idx}&tab=output&subtab=build"
        ),
        "jobs": (
            f"/studio/partial/export?doc_id={encoded_doc}&library={encoded_lib}&page={page_idx}&tab=jobs&subtab=jobs"
        ),
    }
    # Header buttons
    tab_buttons = Div(
        Button(
            "📝 Trascrizione",
            onclick="switchTab('transcription')",
            id="tab-button-transcription",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'transcription' else ''}",
        ),
        Button(
            "📂 Snippets",
            onclick="switchTab('snippets')",
            id="tab-button-snippets",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'snippets' else ''}",
        ),
        Button(
            "📝 History",
            onclick="switchTab('history')",
            id="tab-button-history",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'history' else ''}",
        ),
        Button(
            "🎨 Visual",
            onclick="switchTab('visual')",
            id="tab-button-visual",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'visual' else ''}",
        ),
        Button(
            "ℹ️ Info",
            onclick="switchTab('info')",
            id="tab-button-info",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'info' else ''}",
        ),
        Button(
            "🖼️ Immagini",
            onclick="switchTab('images')",
            id="tab-button-images",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'images' else ''}",
        ),
        Button(
            "📄 Output",
            onclick="switchTab('output')",
            id="tab-button-output",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'output' else ''}",
        ),
        Button(
            "🧰 Job",
            onclick="switchTab('jobs')",
            id="tab-button-jobs",
            cls=f"tab-button studio-tab{' studio-tab-active' if safe_active_tab == 'jobs' else ''}",
        ),
        id="studio-tablist",
        cls="studio-tablist whitespace-nowrap",
    )
    buttons = Div(
        Button(
            "‹",
            type="button",
            id="studio-tab-scroll-left",
            cls="app-btn app-btn-neutral px-2 py-1 text-sm",
            aria_label="Scorri tab a sinistra",
            title="Scorri tab a sinistra",
        ),
        Div(
            tab_buttons,
            id="studio-tablist-scroll",
            cls="flex-1 overflow-x-auto overflow-y-hidden",
            style="scrollbar-width:none;-ms-overflow-style:none;",
        ),
        Button(
            "›",
            type="button",
            id="studio-tab-scroll-right",
            cls="app-btn app-btn-neutral px-2 py-1 text-sm",
            aria_label="Scorri tab a destra",
            title="Scorri tab a destra",
        ),
        cls="studio-tablist-shell flex items-center gap-2",
    )

    tab_contents = Div(
        Div(
            Div(
                *transcription_tab_content(doc_id, library, page_idx, error_msg=ocr_error, is_loading=is_ocr_loading),
                id="transcription-container",
                cls="relative h-full",
            ),
            id="tab-content-transcription",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'transcription' else ''}",
        ),
        Div(
            *snippets_tab_content(doc_id, page_idx, library),
            id="tab-content-snippets",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'snippets' else ''}",
        ),
        Div(
            *history_tab_content(doc_id, page_idx, library, info_message=history_message),
            id="tab-content-history",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'history' else ''}",
        ),
        Div(
            *visual_tab_content(),
            id="tab-content-visual",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'visual' else ''}",
        ),
        Div(
            *info_tab_content(meta, total_pages, manifest_json, page_idx, doc_id, library),
            id="tab-content-info",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'info' else ''}",
        ),
        Div(
            (
                export_fragment
                if export_fragment is not None and safe_active_tab == "images"
                else Div(
                    "Apri il tab Immagini per gestire miniature e ottimizzazione.",
                    cls="text-sm text-slate-500 dark:text-slate-400 p-2",
                )
            ),
            id="tab-content-images",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'images' else ''}",
            data_export_loaded="1" if (export_fragment is not None and safe_active_tab == "images") else "0",
            data_export_url=export_urls["images"],
            data_export_placeholder="Apri il tab Immagini per gestire miniature e ottimizzazione.",
        ),
        Div(
            (
                export_fragment
                if export_fragment is not None and safe_active_tab == "output"
                else Div(
                    "Apri il tab Output per configurare e creare PDF.",
                    cls="text-sm text-slate-500 dark:text-slate-400 p-2",
                )
            ),
            id="tab-content-output",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'output' else ''}",
            data_export_loaded="1" if (export_fragment is not None and safe_active_tab == "output") else "0",
            data_export_url=export_urls["output"],
            data_export_placeholder="Apri il tab Output per configurare e creare PDF.",
        ),
        Div(
            (
                export_fragment
                if export_fragment is not None and safe_active_tab == "jobs"
                else Div(
                    "Apri il tab Job per monitorare la coda processi.",
                    cls="text-sm text-slate-500 dark:text-slate-400 p-2",
                )
            ),
            id="tab-content-jobs",
            cls=f"tab-content h-full{' hidden' if safe_active_tab != 'jobs' else ''}",
            data_export_loaded="1" if (export_fragment is not None and safe_active_tab == "jobs") else "0",
            data_export_url=export_urls["jobs"],
            data_export_placeholder="Apri il tab Job per monitorare la coda processi.",
        ),
        cls="studio-tabpanes flex-1 overflow-y-auto p-4",
    )

    doc_js = json.dumps(doc_id)
    lib_js = json.dumps(library)
    default_tab_js = json.dumps(safe_active_tab)
    switch_script = Script(
        f"""(function() {{
            const ALLOWED_TABS = new Set([
                'transcription', 'snippets', 'history', 'visual', 'info', 'images', 'output', 'jobs'
            ]);
            const docId = {doc_js};
            const library = {lib_js};
            const defaultTab = {default_tab_js};

            function currentPageFromUrl() {{
                try {{
                    const pageRaw = new URL(window.location.href).searchParams.get('page');
                    const page = Number.parseInt(pageRaw || '', 10);
                    return Number.isFinite(page) && page > 0 ? page : {page_idx};
                }} catch (_e) {{
                    return {page_idx};
                }}
            }}

            function updateUrlTab(tab) {{
                try {{
                    const url = new URL(window.location.href);
                    url.searchParams.set('tab', tab);
                    window.history.replaceState({{}}, '', url);
                }} catch (_e) {{
                    // no-op
                }}
            }}

            function saveContext(tab) {{
                const page = currentPageFromUrl();
                const body = new URLSearchParams();
                body.set('doc_id', docId);
                body.set('library', library);
                body.set('page', String(page));
                body.set('tab', tab);
                fetch('/api/studio/context/save', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' }},
                    body: body.toString(),
                    credentials: 'same-origin'
                }}).catch(() => null);
            }}

            function buildExportUrl(baseUrl, params) {{
                if (!baseUrl) return '';
                const extra = params || {{}};
                try {{
                    const url = new URL(baseUrl, window.location.origin);
                    Object.entries(extra).forEach(([key, value]) => {{
                        if (value === undefined || value === null || String(value) === '') return;
                        url.searchParams.set(String(key), String(value));
                    }});
                    return url.pathname + url.search;
                }} catch (_e) {{
                    return baseUrl;
                }}
            }}

            function unloadInactiveExportPanes(activeTab) {{
                const exportTabs = ['images', 'output', 'jobs'];
                exportTabs.forEach((name) => {{
                    if (name === activeTab) return;
                    const pane = document.getElementById('tab-content-' + name);
                    if (!pane || pane.dataset.exportLoaded !== '1') return;
                    const panel = pane.querySelector('#studio-export-panel');
                    if (panel && window.htmx) {{
                        try {{ htmx.trigger(panel, 'htmx:abort'); }} catch (_e) {{ /* no-op */ }}
                    }}
                    const placeholder = pane.dataset.exportPlaceholder || '';
                    pane.innerHTML = (
                        '<div class="text-sm text-slate-500 dark:text-slate-400 p-2">'
                        + placeholder
                        + '</div>'
                    );
                    pane.dataset.exportLoaded = '0';
                }});
            }}

            function updateTabScrollControls() {{
                const strip = document.getElementById('studio-tablist-scroll');
                const leftBtn = document.getElementById('studio-tab-scroll-left');
                const rightBtn = document.getElementById('studio-tab-scroll-right');
                if (!strip || !leftBtn || !rightBtn) return;
                const maxScroll = Math.max(0, strip.scrollWidth - strip.clientWidth);
                const hasOverflow = maxScroll > 2;
                if (!hasOverflow) {{
                    leftBtn.classList.add('hidden');
                    rightBtn.classList.add('hidden');
                    return;
                }}
                leftBtn.classList.remove('hidden');
                rightBtn.classList.remove('hidden');
                const left = strip.scrollLeft;
                leftBtn.disabled = left <= 1;
                rightBtn.disabled = left >= maxScroll - 1;
                leftBtn.classList.toggle('opacity-40', leftBtn.disabled);
                leftBtn.classList.toggle('cursor-not-allowed', leftBtn.disabled);
                rightBtn.classList.toggle('opacity-40', rightBtn.disabled);
                rightBtn.classList.toggle('cursor-not-allowed', rightBtn.disabled);
            }}

            function setupTabScroller() {{
                const strip = document.getElementById('studio-tablist-scroll');
                const leftBtn = document.getElementById('studio-tab-scroll-left');
                const rightBtn = document.getElementById('studio-tab-scroll-right');
                if (!strip || !leftBtn || !rightBtn) return;

                if (!document.getElementById('studio-tablist-scroll-style')) {{
                    const style = document.createElement('style');
                    style.id = 'studio-tablist-scroll-style';
                    style.textContent = '#studio-tablist-scroll::-webkit-scrollbar{{display:none;}}';
                    document.head.appendChild(style);
                }}

                if (strip.dataset.bound !== '1') {{
                    strip.dataset.bound = '1';
                    strip.addEventListener('scroll', updateTabScrollControls, {{ passive: true }});
                }}
                if (leftBtn.dataset.bound !== '1') {{
                    leftBtn.dataset.bound = '1';
                    leftBtn.addEventListener('click', () => {{
                        strip.scrollBy({{ left: -220, behavior: 'smooth' }});
                        window.setTimeout(updateTabScrollControls, 180);
                    }});
                }}
                if (rightBtn.dataset.bound !== '1') {{
                    rightBtn.dataset.bound = '1';
                    rightBtn.addEventListener('click', () => {{
                        strip.scrollBy({{ left: 220, behavior: 'smooth' }});
                        window.setTimeout(updateTabScrollControls, 180);
                    }});
                }}
                if (!window.__studioTabScrollerResizeBound) {{
                    window.__studioTabScrollerResizeBound = true;
                    window.addEventListener('resize', updateTabScrollControls, {{ passive: true }});
                }}
                updateTabScrollControls();
            }}

            function switchTab(t, opts) {{
                const options = opts || {{}};
                const tab = ALLOWED_TABS.has(String(t || '').trim()) ? String(t).trim() : 'transcription';
                document.querySelectorAll('.tab-content').forEach((el) => el.classList.add('hidden'));
                document.querySelectorAll('.tab-button').forEach((btn) => {{
                    btn.classList.remove('studio-tab-active');
                }});

                const target = document.getElementById('tab-content-' + tab);
                if (!target) return;
                target.classList.remove('hidden');

                const btn = document.getElementById('tab-button-' + tab);
                if (btn) {{
                    btn.classList.add('studio-tab-active');
                    if (typeof btn.scrollIntoView === 'function') {{
                        btn.scrollIntoView({{ behavior: 'smooth', inline: 'nearest', block: 'nearest' }});
                    }}
                }}

                if (options.updateUrl !== false) updateUrlTab(tab);
                if (options.persist !== false) saveContext(tab);
                document.body.dataset.studioActiveTab = tab;
                unloadInactiveExportPanes(tab);
                updateTabScrollControls();

                if (tab === 'images' || tab === 'output' || tab === 'jobs') {{
                    const loaded = target.dataset.exportLoaded === '1';
                    const shouldReload = options.reloadExport === true;
                    const exportUrl = target.dataset.exportUrl || '';
                    if ((!loaded || shouldReload) && exportUrl) {{
                        target.dataset.exportLoaded = '1';
                        try {{
                            const finalUrl = buildExportUrl(exportUrl, options.exportParams);
                            htmx.ajax('GET', finalUrl, {{ target: '#tab-content-' + tab, swap: 'innerHTML' }});
                        }} catch (e) {{
                            console.error('export-load-err', e);
                            target.dataset.exportLoaded = '0';
                        }}
                    }}
                }}
            }}

            window.switchTab = switchTab;
            setupTabScroller();
            switchTab(defaultTab, {{ persist: false, updateUrl: true }});
        }})();"""
    )

    main_panel = Div(buttons, tab_contents, switch_script, cls="flex flex-col h-full overflow-hidden")

    overlay = None
    overlay_script = None
    if is_ocr_loading:
        encoded_doc = quote(doc_id, safe="")
        encoded_lib = quote(library, safe="")
        hx_path = f"/api/check_ocr_status?doc_id={encoded_doc}&library={encoded_lib}&page={page_idx}"

        overlay = Div(
            Div(
                Div(
                    cls="animate-spin rounded-full h-8 w-8 border-b-2 mb-4",
                    style="border-color: var(--app-accent);",
                ),
                Span(
                    "AI in ascolto...",
                    cls="font-bold tracking-widest uppercase text-[10px]",
                    style="color: var(--app-primary);",
                ),
                cls="flex flex-col items-center justify-center h-full",
            ),
            cls=(
                "absolute inset-0 bg-white/90 dark:bg-slate-950/90 backdrop-blur-[2px] z-50 rounded-xl "
                "flex items-center justify-center pointer-events-auto"
            ),
            hx_get=hx_path,
            hx_trigger="every 2s",
            hx_target="#studio-right-panel",
            hx_swap="outerHTML",
        )

        doc_js = json.dumps(doc_id)
        lib_js = json.dumps(library)
        timeout_ms = 60000
        overlay_script = Script(
            f"""(function() {{
                const panel = document.getElementById('studio-right-panel');
                if (!panel) return;
                const docId = {doc_js};
                const libId = {lib_js};
                const pageIdx = {page_idx};
                const timeoutMs = {timeout_ms};
                let resolved = false;
                const timeoutId = window.setTimeout(() => {{
                    if (!resolved) {{
                        console.warn(
                            'OCR poll appears stuck for doc',
                            docId,
                            'lib', libId,
                            'page', pageIdx,
                            'after', timeoutMs, 'ms'
                        );
                    }}
                }}, timeoutMs);

                const handler = (event) => {{
                    if (event?.detail?.target?.id !== 'studio-right-panel') {{
                        return;
                    }}
                    resolved = true;
                    window.clearTimeout(timeoutId);
                    console.debug('OCR poll response received for doc', docId, 'page', pageIdx, event.detail);
                    panel.removeEventListener('htmx:afterSwap', handler);
                }};

                panel.addEventListener('htmx:afterSwap', handler);
            }})();"""
        )

    wrapper_children = [main_panel]
    if overlay:
        wrapper_children.append(overlay)
    if overlay_script:
        wrapper_children.append(overlay_script)

    return Div(*wrapper_children, cls="relative h-full")
