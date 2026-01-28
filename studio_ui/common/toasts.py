"""Shared utilities for rendering toast notifications in the FastHTML UI."""

from __future__ import annotations

import json

from fasthtml.common import Div, Script

_TONE_STYLES = {
    "success": "bg-emerald-900/95 border border-emerald-500/70 text-emerald-50 shadow-emerald-500/40",
    "info": "bg-slate-900/90 border border-slate-600/80 text-slate-50 shadow-slate-700/50",
    "danger": "bg-rose-900/90 border border-rose-500/70 text-rose-50 shadow-rose-500/40",
}
_ICONS = {"success": "✅", "info": "ℹ️", "danger": "⚠️"}


def build_toast(message: str, tone: str = "success") -> tuple[Div, Script]:
    """Return hidden placeholder and script that appends a toast to the stack."""
    tone_classes = _TONE_STYLES.get(tone, _TONE_STYLES["info"])

    js_msg = json.dumps(message)
    js_icon = json.dumps(_ICONS.get(tone, "ℹ️"))
    js_tone = json.dumps(tone_classes)

    script = Script(
        f"""
        (function () {{
            try {{
                const stack = document.getElementById('studio-toast-stack');
                if (!stack) return;
                const toast = document.createElement('div');
                toast.className = 'pointer-events-auto studio-toast-entry flex items-center gap-3 rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-sm opacity-0 -translate-y-3 scale-95 transition-all duration-300 ' + {js_tone};
                toast.setAttribute('role', 'status');
                toast.setAttribute('aria-live', 'polite');
                toast.innerHTML = `<span class="text-lg leading-none">${{ {js_icon} }}</span><span class="text-sm font-semibold text-current">${{ {js_msg} }}</span>`;
                stack.appendChild(toast);
                requestAnimationFrame(() => {{
                    toast.classList.remove('opacity-0', '-translate-y-3', 'scale-95');
                    toast.classList.add('opacity-100', 'translate-y-0', 'scale-100');
                }});
                const dismiss = () => {{
                    toast.classList.add('opacity-0', 'translate-y-3');
                    toast.classList.remove('opacity-100', 'translate-y-0');
                }};
                setTimeout(dismiss, 4800);
                setTimeout(() => {{ if (stack.contains(toast)) toast.remove(); }}, 5600);
            }} catch (err) {{ console.error('Toast render error', err); }}
        }})();
        """
    )

    return Div("", cls="hidden"), script
