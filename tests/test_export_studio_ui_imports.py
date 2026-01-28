def test_studio_routes_importable():
    """Ensure the new FastHTML studio routes module imports."""
    from studio_ui.routes.studio import setup_studio_routes

    assert callable(setup_studio_routes)


def test_studio_tabs_importable():
    """Ensure the studio tabs component imports."""
    from studio_ui.components.studio.tabs import render_studio_tabs

    assert callable(render_studio_tabs)
