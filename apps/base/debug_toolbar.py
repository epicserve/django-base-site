from debug_toolbar.middleware import show_toolbar as default_show_toolbar

# Set by the SPA (see frontend/js/utils/debugToolbar.js) when a developer turns the toolbar on from the user menu.
# A cookie, not a setting, so nobody has to edit settings or restart anything.
ENABLED_COOKIE = "debug_toolbar"


def show_toolbar(request) -> bool:
    """Show the toolbar only when it passes the default DEBUG + INTERNAL_IPS check and was turned on."""
    return request.COOKIES.get(ENABLED_COOKIE) == "1" and default_show_toolbar(request)
