def test_history_refresh_script_points_to_history_panel():
    """HTMX helper should request the history tab swap."""
    from studio_ui.common.htmx import history_refresh_script

    script = history_refresh_script("Doc", "Lib", 5)

    assert "#tab-content-history" in str(script)
