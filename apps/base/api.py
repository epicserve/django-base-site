from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import dateformat
from django.utils.timezone import now

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.base.permissions import require_superuser
from apps.base.templatetags.vite import _get_manifest, vite_settings
from apps.base.utils.email import send_email
from apps.base.utils.timezones import get_timezone_label
from apps.organizations.models import Organization
from apps.organizations.session import get_member_count, get_owner_count

router = Router(tags=["app"])


def _get_app_version() -> str:
    if vite_settings.VITE_DEV_MODE is True:
        return "dev"
    try:
        manifest = _get_manifest()
    except (FileNotFoundError, ValueError):
        return "unknown"
    entry = manifest.get("js/app.js") or {}
    return entry.get("file", "unknown")


@router.get("/version/", auth=None)
def get_version(request):
    return {"version": _get_app_version()}


@router.get("/app-context/", auth=None)
def app_context(request):
    if not request.user.is_authenticated:
        return {
            "user": None,
            "org": None,
            "organizations": [],
            "orgMemberCount": 0,
            "orgOwnerCount": 0,
            "siteName": getattr(settings, "SITE_NAME", ""),
            "instance": getattr(settings, "INSTANCE", ""),
            "signupOpen": getattr(settings, "ACCOUNT_SIGNUP_OPEN", False),
            "version": _get_app_version(),
        }

    user = request.user
    org = getattr(request, "org", None)
    user_orgs = [
        {"id": o.pk, "name": o.name, "slug": o.slug} for o in Organization.objects.filter(organizationmember__user=user)
    ]
    org_data = None
    if org and org.pk:
        org_data = {"id": org.id, "name": org.name, "slug": org.slug, "is_owner": org.is_owner}

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "timezone": user.timezone,
            "timezone_display": get_timezone_label(user.timezone),
            "avatar_url": user.avatar_url,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_hijacked": getattr(user, "is_hijacked", False),
            "organizations": user_orgs,
        },
        "org": org_data,
        "organizations": user_orgs,
        "orgMemberCount": get_member_count(request),
        "orgOwnerCount": get_owner_count(request),
        "siteName": getattr(settings, "SITE_NAME", ""),
        "instance": getattr(settings, "INSTANCE", ""),
        "signupOpen": getattr(settings, "ACCOUNT_SIGNUP_OPEN", False),
        "version": _get_app_version(),
    }


@router.get("/send-test-email/staff-users/")
def test_email_staff_users(request):
    require_superuser(request)
    User = get_user_model()
    users = User.objects.filter(is_staff=True).order_by("first_name", "last_name", "email")
    return [{"id": u.id, "full_name": u.get_full_name() or u.username, "email": u.email} for u in users]


class SendTestEmailIn(Schema):
    user_id: int


@router.post("/send-test-email/")
def send_test_email(request, payload: SendTestEmailIn):
    require_superuser(request)
    User = get_user_model()
    try:
        recipient = User.objects.get(pk=payload.user_id, is_staff=True)
    except User.DoesNotExist as exc:
        raise HttpError(400, "Invalid recipient.") from exc

    date_time = dateformat.format(now(), settings.SHORT_DATETIME_FORMAT)
    subject = f"Django Test Email ({date_time})"
    debug_settings = [
        (name, getattr(settings, name, None))
        for name in (
            "SETTINGS_MODULE",
            "EMAIL_HOST",
            "EMAIL_HOST_USER",
            "EMAIL_PORT",
            "EMAIL_CONFIG",
            "EMAIL_BACKEND",
        )
    ]
    context = {"subject": subject, "date_time": date_time, "debug_settings": debug_settings}
    send_email(
        recipient,
        recipients=[recipient],
        subject=subject,
        base_template_name="emails/test_email",
        context=context,
    )
    return {"message": f"Test email sent to {recipient.get_full_name() or recipient.username} ({recipient.email})"}
