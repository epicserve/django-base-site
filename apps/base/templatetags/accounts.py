import json

from django import template
from django.utils.safestring import mark_safe

from apps.base.utils.timezones import get_timezone_label
from apps.organizations.models import Organization

register = template.Library()


@register.simple_tag()
def get_org_js_object(request):
    data = {
        "id": request.org.id,
        "name": request.org.name,
        "slug": request.org.slug,
        "is_owner": request.org.is_owner,
        "type": "org" if request.org.id else "user",
    }
    return mark_safe(json.dumps(data))  # noqa: S308


@register.simple_tag()
def get_user_js_object(request):
    data = {
        "id": request.user.id,
        "username": request.user.username,
        "name": request.user.get_full_name(),
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "timezone": request.user.timezone,
        "timezone_display": get_timezone_label(request.user.timezone),
    }
    user_orgs_qs = Organization.objects.prefetch_related("organizationmember_set").filter(
        organizationmember__user=request.user
    )
    user_orgs = []
    for org in user_orgs_qs:
        user_orgs.append({"id": org.pk, "name": org.name, "slug": org.slug})
    data["organizations"] = user_orgs
    return mark_safe(json.dumps(data))  # noqa: S308


@register.filter
def timezone_label(iana_key):
    """Template filter to get friendly timezone label."""
    return get_timezone_label(iana_key)


@register.simple_tag()
def get_timezone_labels_json():
    """Return the timezone labels mapping as a JSON object for use in JS."""
    from apps.base.utils.timezones import TIMEZONE_LABELS

    return json.dumps(TIMEZONE_LABELS, ensure_ascii=False)
