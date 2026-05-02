from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("organizations/_debug_info.html", takes_context=True)
def organization_debug_info(context):
    user = context.get("user")
    show = (
        user is not None
        and (user.is_superuser or getattr(user, "is_hijacked", False))
        and getattr(settings, "SHOW_ORG_DEBUG_INFO", False) is True
    )
    return {
        "request": context.get("request"),
        "org": context.get("org"),
        "org_owner_count": context.get("org_owner_count"),
        "org_member_count": context.get("org_member_count"),
        "show_debug_info": show,
    }
