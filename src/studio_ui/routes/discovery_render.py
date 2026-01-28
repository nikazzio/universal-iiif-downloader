"""Rendering helpers for the Discovery routes.

Keeping UI rendering separate makes the route handlers small and testable.
"""

from fasthtml.common import H2, H3, Button, Div, Form, Input, Label, Option, P, Select, Span, Table, Tbody, Td, Th, Tr


def discovery_form() -> Div:
    """Form component for discovery searches."""
    libraries = [
        ("Vaticana (BAV)", "Vaticana"),
        ("Gallica (BnF)", "Gallica"),
        ("Bodleian (Oxford)", "Bodleian"),
        ("Altro / URL Diretto", "Unknown"),
    ]

    return Div(
        H3("🔎 Ricerca per Segnatura", cls="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4"),
        Form(
            Div(
                # Library selector
                Div(
                    Label(
                        "Biblioteca",
                        for_="lib-select",
                        cls="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1",
                    ),
                    Select(
                        *[Option(label, value=value) for label, value in libraries],
                        id="lib-select",
                        name="library",
                        cls=(
                            "w-full px-3 py-2 border border-gray-300 "
                            "dark:border-gray-600 rounded bg-white dark:bg-gray-800 "
                            "dark:text-white"
                        ),
                    ),
                    cls="w-1/3",
                ),
                # Input
                Div(
                    Label(
                        "Segnatura, ID o URL",
                        for_="shelf-input",
                        cls="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1",
                    ),
                    Input(
                        type="text",
                        id="shelf-input",
                        name="shelfmark",
                        placeholder="es. Urb.lat.1779 o btv1b10033406t",
                        cls=(
                            "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white "
                            "dark:bg-gray-800 dark:text-white shadow-sm",
                        ),
                    ),
                    cls="w-2/3",
                ),
                cls="flex gap-4 mb-4",
            ),
            Button(
                "🔍 Analizza Documento",
                type="submit",
                cls=(
                    "w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded "
                    "transition-all shadow-md active:scale-95",
                ),
            ),
            hx_post="/api/resolve_manifest",
            hx_target="#discovery-preview",
            hx_indicator="#resolve-spinner",
        ),
        # Spinner
        Div(
            Div(cls="inline-block w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"),
            id="resolve-spinner",
            cls="htmx-indicator flex justify-center mt-6",
        ),
        cls="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm",
    )


def discovery_content() -> Div:
    """Top-level content block for the discovery page."""
    return Div(
        H2("🛰️ Discovery & Download", cls="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6"),
        discovery_form(),
        Div(id="discovery-preview", cls="mt-8"),
        cls="p-6 max-w-5xl mx-auto",
    )


def render_preview(data: dict) -> Div:
    """Render preview block for a manifest."""
    return Div(
        H3(
            f"📖 {data['label']}",
            cls="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2",
        ),
        P(
            data.get("description", ""),
            cls="text-gray-600 dark:text-gray-400 mb-4 italic line-clamp-3",
        ),
        Div(
            Table(
                Tbody(
                    Tr(
                        Th("ID", cls="text-left py-1 pr-4 font-medium text-gray-500"),
                        Td(data["id"], cls="dark:text-gray-300"),
                    ),
                    Tr(
                        Th("Library", cls="text-left py-1 pr-4 font-medium text-gray-500"),
                        Td(data["library"], cls="dark:text-gray-300"),
                    ),
                    Tr(
                        Th("Pagine", cls="text-left py-1 pr-4 font-medium text-gray-500"),
                        Td(str(data["pages"]), cls="dark:text-gray-300"),
                    ),
                    Tr(
                        Th("Manifest", cls="text-left py-1 pr-4 font-medium text-gray-500"),
                        Td(
                            data["url"],
                            cls="text-xs truncate max-w-sm text-blue-500",
                        ),
                    ),
                ),
                cls="w-full mb-6",
            ),
            Form(
                Input(type="hidden", name="manifest_url", value=data["url"]),
                Input(type="hidden", name="doc_id", value=data["id"]),
                Input(type="hidden", name="library", value=data["library"]),
                Button(
                    Span("🚀 Avvia Download", cls="font-bold"),
                    type="submit",
                    cls=(
                        "w-full py-4 bg-green-600 hover:bg-green-700 text-white rounded-lg "
                        "transition-all shadow-lg hover:shadow-xl active:scale-95 flex items-center "
                        "justify-center gap-2",
                    ),
                ),
                hx_post="/api/start_download",
                hx_target="#discovery-preview",
                hx_swap="innerHTML",
            ),
            cls=(
                "bg-gray-50 dark:bg-gray-900 p-6 rounded-lg border-2 border-dashed "
                "border-indigo-200 dark:border-indigo-900",
            ),
        ),
        cls="animate-in fade-in slide-in-from-top-4 duration-300",
    )


def render_download_status(download_id: str, doc_id: str) -> Div:
    """Render the initial download status fragment (polling placeholder)."""
    return Div(
        Div(
            Span("🚀", cls="text-2xl mr-2"),
            Span(f"Download di '{doc_id}' avviato...", cls="font-bold"),
            cls="flex items-center text-indigo-600 dark:text-indigo-400 mb-2",
        ),
        Div(
            "Inizializzazione worker...",
            hx_get=f"/api/download_status/{download_id}",
            hx_trigger="every 1s",
            hx_swap="outerHTML",
        ),
        cls=("bg-indigo-50 dark:bg-indigo-950 p-6 rounded-lg border border-indigo-200 dark:border-indigo-800"),
    )
