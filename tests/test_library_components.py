from studio_ui.components.library import render_library_card, render_library_page


def _base_doc(**overrides):
    doc = {
        "id": "DOC_CARD_PDF",
        "library": "Gallica",
        "display_title": "Test card PDF",
        "asset_state": "complete",
        "item_type": "manoscritto",
        "total_canvases": 12,
        "downloaded_canvases": 12,
        "missing_pages": [],
        "reference_text": "",
        "source_detail_url": "",
        "date_label": "",
        "language_label": "",
        "shelfmark": "Shelf.1",
        "thumbnail_url": "",
        "has_native_pdf": None,
        "pdf_local_available": False,
    }
    doc.update(overrides)
    return doc


def test_library_card_shows_pdf_presence_badges():
    """Cards should expose native/local PDF availability clearly."""
    rendered = repr(
        render_library_card(
            _base_doc(
                pdf_source="native",
                has_native_pdf=True,
                pdf_local_available=True,
                pdf_local_count=3,
            )
        )
    )
    assert "Sorgente PDF:" in rendered
    assert "nativa" in rendered
    assert "PDF locali:" in rendered
    assert "3" in rendered


def test_library_card_shows_pdf_absence_badges():
    """Cards should expose missing PDF availability clearly."""
    rendered = repr(
        render_library_card(
            _base_doc(
                pdf_source="images",
                has_native_pdf=False,
                pdf_local_available=False,
                pdf_local_count=0,
            )
        )
    )
    assert "Sorgente PDF:" in rendered
    assert "da immagini" in rendered
    assert "PDF locali:" in rendered
    assert "0" in rendered


def test_library_page_includes_filter_persistence_script():
    """Library page should include client-side filter persistence bootstrap."""
    rendered = repr(render_library_page([]))
    assert "ui.library.filters.v1" in rendered
    assert "__libraryFiltersPersistenceBootstrapped" in rendered
    assert "htmx.ajax('GET', url" in rendered
    assert 'const DEFAULT_MODE = "operativa";' in rendered


def test_library_page_reset_control_clears_persisted_filters():
    """Reset action must expose a stable id used by persistence script."""
    rendered = repr(render_library_page([]))
    assert 'id="library-reset-filters"' in rendered


def test_library_page_mode_switch_outside_filters():
    """Mode switch should be visually separated from filter form and keep mode in form state."""
    rendered = repr(render_library_page([]))
    assert "Modalita Libreria" in rendered
    assert 'name="mode"' in rendered
    assert 'type="hidden"' in rendered
    assert 'value="operativa"' in rendered
    assert rendered.index("Modalita Libreria") < rendered.index('id="library-filters"')


def test_library_page_uses_configurable_default_mode_in_script():
    """Persistence script should honor current default mode for query serialization."""
    rendered = repr(render_library_page([], default_mode="archivio", mode="archivio"))
    assert 'const DEFAULT_MODE = "archivio";' in rendered


def test_library_card_truncates_long_title():
    """Card title should be truncated for very long labels."""
    long_title = "Titolo molto lungo " * 10
    rendered = repr(render_library_card(_base_doc(display_title=long_title)))
    assert "[...]" in rendered
