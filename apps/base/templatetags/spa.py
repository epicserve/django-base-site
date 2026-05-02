from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def spa_url(name, **kwargs):
    """
    Resolve a Vue Router path from settings.SPA_URLS.

    Mirrors Django's `{% url %}` tag for SPA-only routes that don't exist as
    Django URL patterns. Raises KeyError (caught by the template engine) if
    `name` isn't registered in SPA_URLS so typos fail loudly.
    """
    template_str = settings.SPA_URLS[name]
    return template_str.format(**kwargs) if kwargs else template_str
