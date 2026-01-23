def test_export_studio_selection_is_session_state_based():
    """Twin selection state is derived from Streamlit session_state keys."""
    from iiif_downloader.ui.pages.export_studio.thumbnail_grid import _selection_key

    assert _selection_key("DOC", 1) == "export_page_DOC_1"
