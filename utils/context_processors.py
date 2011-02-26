from django.conf import settings


def site_name(request):
    """
    Adds the site_name from settings to the context variables.

    """
    return {'site_name': getattr(settings, 'SITE_NAME', 'Set your SITE_NAME in your settings file')}
