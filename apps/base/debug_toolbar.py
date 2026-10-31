from django.conf import settings

# Set by the SPA (see frontend/js/utils/debugToolbar.js) when a developer turns the toolbar on from the user menu.
# A cookie, not a setting, so nobody has to edit settings or restart anything.
ENABLED_COOKIE = "debug_toolbar"


def show_toolbar(request) -> bool:
    """
    Show the toolbar only in DEBUG, for an INTERNAL_IPS address, and once it was turned on.

    The first two checks are the toolbar's own default. They're repeated here rather than imported because
    importing debug_toolbar fails when DEBUG is off and the app isn't installed, as in CI.
    """
    return (
        request.COOKIES.get(ENABLED_COOKIE) == "1"
        and settings.DEBUG is True
        and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS
    )
