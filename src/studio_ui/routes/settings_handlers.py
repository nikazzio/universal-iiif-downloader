from studio_ui.common.toasts import build_toast
from studio_ui.components.layout import base_layout
from studio_ui.components.settings import settings_content
from universal_iiif_core.config_manager import get_config_manager


def settings_page(request):
    """Renderizza la pagina delle impostazioni."""
    return base_layout(title="Impostazioni - Universal IIIF", content=settings_content(), active_page="settings")


async def save_settings(request):
    """Salva le impostazioni inviate dal form."""
    form = await request.form()
    cm = get_config_manager()

    try:
        # 1. Update API Keys
        if "api_openai" in form:
            cm.set_api_key("openai", form["api_openai"])
        if "api_anthropic" in form:
            cm.set_api_key("anthropic", form["api_anthropic"])
        if "api_google_vision" in form:
            cm.set_api_key("google_vision", form["api_google_vision"])
        if "api_huggingface" in form:
            cm.set_api_key("huggingface", form["api_huggingface"])

        # 2. Update Defaults
        cm.set_setting("defaults.default_library", form.get("default_library", "Vaticana"))
        cm.set_setting("defaults.preferred_ocr_engine", form.get("preferred_ocr_engine", "openai"))

        # 3. Update System
        if "request_timeout" in form:
            cm.set_setting("system.request_timeout", int(form["request_timeout"]))

        # Persist to disk
        cm.save()

        # Feedback UI
        return build_toast("Impostazioni salvate con successo!", "success")

    except Exception as e:
        return build_toast(f"Errore nel salvataggio: {e}", "danger")
