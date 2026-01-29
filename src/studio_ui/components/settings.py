from fasthtml.common import H1, H3, Button, Div, Form, Input, Label, Option, P, Select, Span

from universal_iiif_core.config_manager import get_config_manager


def settings_content() -> Div:
    """Renderizza il pannello delle impostazioni completo."""
    cm = get_config_manager()

    # Helper per creare sezioni
    def section_header(title, icon):
        return Div(
            Span(icon, cls="text-xl mr-2"),
            H3(title, cls="text-lg font-bold text-slate-100"),
            cls="flex items-center mb-4 pb-2 border-b border-slate-700",
        )

    # Helper per Input generici
    def setting_input(label, name, value, type="text", help_text=""):
        return Div(
            Label(label, cls="block text-sm font-medium text-slate-300 mb-1"),
            Input(
                type=type,
                name=name,
                value=value or "",
                cls="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-100 focus:border-blue-500 outline-none transition-colors",
            ),
            P(help_text, cls="text-xs text-slate-500 mt-1") if help_text else "",
            cls="mb-4",
        )

    # 1. API Keys Section
    api_keys = Div(
        section_header("API Keys OCR", "🔑"),
        Div(
            setting_input("OpenAI API Key", "api_openai", cm.get_api_key("openai"), "password"),
            setting_input("Anthropic API Key", "api_anthropic", cm.get_api_key("anthropic"), "password"),
            setting_input("Google Vision API Key", "api_google_vision", cm.get_api_key("google_vision"), "password"),
            setting_input("HuggingFace Token", "api_huggingface", cm.get_api_key("huggingface"), "password"),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        cls="bg-slate-800 p-6 rounded-lg shadow-sm mb-6",
    )

    # 2. Preferenze Generali
    defaults = cm.get_setting("defaults", {})
    system = cm.get_setting("system", {})

    general = Div(
        section_header("Preferenze di Sistema", "⚙️"),
        Div(
            setting_input("Libreria di Default", "default_library", defaults.get("default_library", "Vaticana")),
            setting_input("Timeout Richieste (sec)", "request_timeout", system.get("request_timeout", 30), "number"),
            Div(
                Label("Engine OCR Preferito", cls="block text-sm font-medium text-slate-300 mb-1"),
                Select(
                    Option("OpenAI", value="openai", selected=defaults.get("preferred_ocr_engine") == "openai"),
                    Option(
                        "Anthropic", value="anthropic", selected=defaults.get("preferred_ocr_engine") == "anthropic"
                    ),
                    Option(
                        "Google Vision",
                        value="google_vision",
                        selected=defaults.get("preferred_ocr_engine") == "google_vision",
                    ),
                    Option(
                        "Kraken (Locale)", value="kraken", selected=defaults.get("preferred_ocr_engine") == "kraken"
                    ),
                    name="preferred_ocr_engine",
                    cls="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-100",
                ),
                cls="mb-4",
            ),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        cls="bg-slate-800 p-6 rounded-lg shadow-sm mb-6",
    )

    # Form Container
    return Div(
        H1("Impostazioni", cls="text-3xl font-bold text-slate-100 mb-8"),
        Form(
            api_keys,
            general,
            # Submit Bar
            Div(
                Button(
                    "💾 Salva Configurazioni",
                    type="submit",
                    cls="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded shadow-lg transition-all transform active:scale-95",
                ),
                cls="sticky bottom-6 flex justify-end",
            ),
            hx_post="/settings/save",
            hx_swap="none",  # Gestito via toast
        ),
        cls="max-w-4xl mx-auto pb-20",
    )
