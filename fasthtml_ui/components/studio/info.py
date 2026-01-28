"""Studio Info and Visual Tabs Components."""

import json

from fasthtml.common import H3, Button, Div, Input, Label, Script, Span
from iiif_downloader.config_manager import get_config_manager


def info_row(label, value):
    val = value[0] if isinstance(value, list) and value else value
    return Div(
        Div(label, cls="text-[10px] font-bold text-gray-400 uppercase tracking-widest"),
        Div(str(val), cls="text-sm font-medium text-gray-800 dark:text-gray-200 break-words"),
    )


def info_tab_content(meta, total_pages):
    return [
        Div(
            info_row("Titolo", meta.get("label", "N/A")),
            info_row("Biblioteca", meta.get("library") or meta.get("attribution", "N/A")),
            info_row("Pagine Totali", str(total_pages)),
            info_row("ID Documento", meta.get("id", "N/A")),
            cls="space-y-4 p-4 bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700",
        )
    ]


DEFAULT_VISUAL_STATE = {
    "brightness": 1.0,
    "contrast": 1.0,
    "saturation": 1.0,
    "hue": 0,
    "invert": False,
    "grayscale": False,
}

DEFAULT_VISUAL_PRESETS = {
    "default": {**DEFAULT_VISUAL_STATE},
    "night": {
        "brightness": 0.9,
        "contrast": 1.3,
        "saturation": 0.9,
        "hue": 0,
        "invert": False,
        "grayscale": False,
    },
    "contrast": {
        "brightness": 1.05,
        "contrast": 1.5,
        "saturation": 1.2,
        "hue": 0,
        "invert": False,
        "grayscale": False,
    },
}


def _visual_control_row(label_text, control_id, min_val, max_val, step, value):
    return Div(
        Label(label_text, for_=control_id, cls="text-xs uppercase font-semibold tracking-wider text-slate-400"),
        Div(
            Input(
                type="range",
                id=control_id,
                min=str(min_val),
                max=str(max_val),
                step=str(step),
                value=str(value),
                cls="w-full h-2 rounded-full bg-slate-200 accent-indigo-500 cursor-pointer",
                **{"data-visual-control": control_id.replace("visual-", "")},
            ),
            Span(f"{value:.2f}", id=f"{control_id}-value", cls="text-xs font-mono text-slate-500 ml-2"),
            cls="flex items-center gap-3 mt-1"
        ),
        cls="space-y-1",
    )


def visual_tab_content():
    cfg = get_config_manager()
    visual_cfg = cfg.get_setting("viewer.visual_filters", {}) or {}
    defaults = {**DEFAULT_VISUAL_STATE, **visual_cfg.get("defaults", {})}
    presets = visual_cfg.get("presets", DEFAULT_VISUAL_PRESETS)
    default_state_json = json.dumps(defaults, ensure_ascii=False)
    presets_json = json.dumps(presets, ensure_ascii=False)

    visual_script = """
        (function(){
            const selectors = [
                '#mirador-viewer canvas',
                '#mirador-viewer img',
                '#mirador-viewer .mirador-viewport canvas',
                '#mirador-viewer .mirador-viewport img',
                '#mirador-viewer .mirador-viewer-window .mirador-window-center canvas',
                '#mirador-viewer .mirador-viewer-window .mirador-window-center img',
            ].join(',');
            const styleId = 'studio-visual-filter-style';
            const defaultState = %s;
            const presets = %s;
            const state = { ...defaultState };

            const ensureStyle = () => {
                let el = document.getElementById(styleId);
                if (!el) {
                    el = document.createElement('style');
                    el.id = styleId;
                    document.head.appendChild(el);
                }
                return el;
            };

            const buildFilter = () => {
                const parts = [
                    `brightness(${state.brightness})`,
                    `contrast(${state.contrast})`,
                    `saturate(${state.saturation})`,
                    `hue-rotate(${state.hue}deg)`
                ];
                if (state.grayscale) parts.push('grayscale(1)');
                if (state.invert) parts.push('invert(1)');
                return parts.join(' ');
            };

            const applyFilters = () => {
                const styleEl = ensureStyle();
                styleEl.textContent = `${selectors} { filter: ${buildFilter()}; transition: filter 0.2s ease; }`;
                updateDisplayValues();
                updateToggleState();
            };

            const updateDisplayValues = () => {
                document.querySelectorAll('[data-visual-control]').forEach(input => {
                    const display = document.getElementById(`${input.id}-value`);
                    if (display) {
                        const key = input.dataset.visualControl;
                        display.textContent = parseFloat(state[key]).toFixed(2);
                    }
                });
            };

            const updateToggleState = () => {
                document.querySelectorAll('[data-visual-toggle]').forEach(btn => {
                    const key = btn.dataset.visualToggle;
                    btn.setAttribute('aria-pressed', state[key]);
                    btn.classList.toggle('bg-indigo-600', state[key]);
                    btn.classList.toggle('text-white', state[key]);
                    btn.classList.toggle('border-slate-300', !state[key]);
                });
            };

            const handleSlider = (event) => {
                const key = event.target.dataset.visualControl;
                state[key] = parseFloat(event.target.value);
                applyFilters();
            };

            const handleToggle = (event) => {
                const key = event.target.dataset.visualToggle;
                state[key] = !state[key];
                applyFilters();
            };

            const applyPreset = (preset) => {
                const values = presets[preset];
                if (!values) return;
                Object.assign(state, values);
                applyFilters();
                document.querySelectorAll('[data-visual-control]').forEach(input => {
                    const key = input.dataset.visualControl;
                    input.value = state[key];
                });
            };

            const initControls = () => {
                document.querySelectorAll('[data-visual-control]').forEach(input => {
                    if (!input.dataset.bound) {
                        input.dataset.bound = 'true';
                        input.addEventListener('input', handleSlider);
                    }
                });
                document.querySelectorAll('[data-visual-toggle]').forEach(btn => {
                    if (!btn.dataset.bound) {
                        btn.dataset.bound = 'true';
                        btn.addEventListener('click', handleToggle);
                    }
                });
                document.querySelectorAll('[data-visual-preset]').forEach(btn => {
                    if (!btn.dataset.bound) {
                        btn.dataset.bound = 'true';
                        btn.addEventListener('click', () => applyPreset(btn.dataset.visualPreset));
                    }
                });
                applyFilters();
            };

            initControls();
            const observeMirador = () => {
                const target = document.getElementById('mirador-viewer');
                if (!target || target.dataset.visualObserver) {
                    return;
                }
                const observer = new MutationObserver(() => {
                    applyFilters();
                });
                observer.observe(target, { childList: true, subtree: true });
                target.dataset.visualObserver = 'true';
            };
            observeMirador();
            document.addEventListener('htmx:afterSwap', (event) => {
                if (event.detail?.target?.id === 'tab-content-visual') {
                    initControls();
                }
            });
        })();
    """ % (default_state_json, presets_json)

    return [
        Div(
            H3("Filtri visuali per la trascrizione", cls="font-bold text-lg text-slate-800 dark:text-slate-200 mb-2"),
            Div(
                "Applica filtri solo all'immagine principale di Mirador, lasciando menu e miniature invariati.",
                cls="text-sm text-slate-500 dark:text-slate-400",
            ),
            Div(
                _visual_control_row("Luminosità", "visual-brightness", 0.6, 1.6, 0.05, defaults.get("brightness", 1.0)),
                _visual_control_row("Contrasto", "visual-contrast", 0.6, 1.6, 0.05, defaults.get("contrast", 1.0)),
                _visual_control_row("Saturazione", "visual-saturation", 0.5, 1.8, 0.05, defaults.get("saturation", 1.0)),
                _visual_control_row("Tonalità (hue)", "visual-hue", -30, 30, 1, defaults.get("hue", 0)),
                cls="space-y-4 mt-4"
            ),
            Div(
                Button(
                    "Inverti colori",
                    type="button",
                    cls="flex-1 text-sm font-semibold uppercase tracking-[0.2em] px-3 py-2 rounded-full border border-slate-300 text-slate-700 dark:text-slate-100",
                    **{"data-visual-toggle": "invert"},
                ),
                Button(
                    "B/N intenso",
                    type="button",
                    cls="flex-1 text-sm font-semibold uppercase tracking-[0.2em] px-3 py-2 rounded-full border border-slate-300 text-slate-700 dark:text-slate-100",
                    **{"data-visual-toggle": "grayscale"},
                ),
                cls="flex gap-3 mt-4"
            ),
            Div(
                Button(
                    "Default",
                    type="button",
                    cls="text-xs font-bold uppercase px-3 py-2 rounded-full bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100 transition",
                    **{"data-visual-preset": "default"},
                ),
                Button(
                    "Lettura notturna",
                    type="button",
                    cls="text-xs font-bold uppercase px-3 py-2 rounded-full bg-gradient-to-r from-indigo-500 to-slate-900 text-white shadow-lg",
                    **{"data-visual-preset": "night"},
                ),
                Button(
                    "Contrasto +",
                    type="button",
                    cls="text-xs font-bold uppercase px-3 py-2 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-700 text-white shadow-lg",
                    **{"data-visual-preset": "contrast"},
                ),
                cls="flex flex-wrap gap-2 mt-4"
            ),
            Div(
                "Mirador mantiene zoom e navigazione: usa la barra di zoom sul viewer quando serve.",
                cls="text-xs text-slate-400 dark:text-slate-500 mt-3",
            ),
            Script(visual_script),
            cls="p-4 bg-white dark:bg-gray-900/60 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-lg space-y-4"
        )
    ]
