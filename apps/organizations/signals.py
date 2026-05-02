from django.contrib.auth import user_logged_in as django_user_logged_in
from django.dispatch import receiver

from allauth.account.signals import user_logged_in
from hijack.signals import hijack_ended, hijack_started

from apps.organizations.session import remove_org, save_counts, save_org_data


def _switch_to_primary_org(request, user):
    from .models import OrganizationMember

    primary_membership = (
        OrganizationMember.objects.filter(user=user, is_primary=True).select_related("organization").first()
    )
    if primary_membership:
        save_org_data(request, primary_membership.organization)
    else:
        remove_org(request)


@receiver(django_user_logged_in)
@receiver(user_logged_in)
def user_logged_in_receiver(sender, **kwargs):
    request = kwargs.get("request")
    if request and hasattr(request, "user") is True:
        save_counts(request)
        _switch_to_primary_org(request, request.user)


@receiver(hijack_started)
def hijack_started_receiver(sender, **kwargs):
    request = kwargs["request"]
    _switch_to_primary_org(request, request.user)


@receiver(hijack_ended)
def hijack_ended_receiver(sender, **kwargs):
    request = kwargs["request"]
    _switch_to_primary_org(request, request.user)
