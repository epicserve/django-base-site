from django.conf import settings
from django.utils import dateformat
from django.utils.timezone import now

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.base.permissions import require_superuser
from apps.base.templatetags.vite import _get_manifest, vite_settings
from apps.base.utils.email import send_email
from apps.base.utils.timezones import get_timezone_label
from apps.billing.access import org_billing_summary
from apps.notifications.services import notify
from apps.organizations.models import Organization, OrganizationMember
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
            "billing": org_billing_summary(None),
        }

    user = request.user
    org_ctx = getattr(request, "org", None)
    user_orgs = [
        {"id": o.pk, "name": o.name, "slug": o.slug} for o in Organization.objects.filter(organizationmember__user=user)
    ]
    org_data = None
    org_instance = None
    if org_ctx and org_ctx.pk:
        org_data = {"id": org_ctx.id, "name": org_ctx.name, "slug": org_ctx.slug, "is_owner": org_ctx.is_owner}
        org_instance = org_ctx.instance

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
        "billing": org_billing_summary(org_instance),
    }


@router.get("/test-notifications/staff-users/")
def test_notifications_staff_users(request):
    require_superuser(request)
    users = User.objects.filter(is_staff=True).order_by("first_name", "last_name", "email")
    return [{"id": u.pk, "full_name": u.get_full_name() or u.username, "email": u.email} for u in users]


class TestNotificationIn(Schema):
    user_id: int
    send_email: bool = True
    send_in_app: bool = True


@router.post("/test-notifications/")
def send_test_notification(request, payload: TestNotificationIn):
    require_superuser(request)
    if not payload.send_email and not payload.send_in_app:
        raise HttpError(400, "Select at least one notification channel.")
    try:
        recipient = User.objects.get(pk=payload.user_id, is_staff=True)
    except User.DoesNotExist as exc:
        raise HttpError(400, "Invalid recipient.") from exc

    date_time = dateformat.format(now(), settings.SHORT_DATETIME_FORMAT)
    subject = f"Test Email ({date_time})"
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

    if payload.send_email:
        send_email(
            recipient,
            recipients=[recipient],
            subject=subject,
            base_template_name="emails/test_email",
            context=context,
        )

    if payload.send_in_app:
        sender_org = request.org.instance if getattr(request.org, "id", None) else None
        if (
            sender_org is not None
            and not OrganizationMember.objects.filter(user=recipient, organization=sender_org).exists()
        ):
            raise HttpError(
                400,
                f"{recipient.get_full_name() or recipient.username} isn't a member of "
                f"{sender_org.name}. Switch to an organization they belong to (or none) "
                f"to send a personal-scope test notification.",
            )
        notify(
            [recipient],
            title="Test Notification",
            body="This is a test notification.",
            actor=request.user,
            organization=sender_org,
        )

    recipient_label = f"{recipient.get_full_name() or recipient.username} ({recipient.email})"
    if payload.send_email and payload.send_in_app:
        return {"message": f"Email + in-app notification sent to {recipient_label}"}
    if payload.send_email:
        return {"message": f"Email sent to {recipient_label}"}
    return {"message": f"In-app notification sent to {recipient_label}"}
