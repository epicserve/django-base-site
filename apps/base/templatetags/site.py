from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag()
def get_site_name():
    return getattr(settings, "SITE_NAME", "Add SITE_NAME to your Django settings.")


@register.filter
def human_duration(seconds):
    if not seconds:
        return "0 min"
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    if h == 0:
        return f"{m} min"
    if m == 0:
        return f"{h} h"
    return f"{h} h {m} min"
