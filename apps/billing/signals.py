"""
Per-seat sync signals.

When members are added/removed from an organization, defer a Stripe quantity
update to after the surrounding DB transaction commits. The deferred call
re-fetches the org by id (the in-memory instance may be stale) and no-ops
when the org has no seat-based subscription.
"""

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.organizations.models import OrganizationMember


@receiver(post_save, sender=OrganizationMember, dispatch_uid="billing.seat_sync_post_save")
@receiver(post_delete, sender=OrganizationMember, dispatch_uid="billing.seat_sync_post_delete")
def _seat_sync(sender, instance, **kwargs):
    if not getattr(settings, "BILLING_ENABLED", False):
        return
    org_id = instance.organization_id
    if not org_id:
        return

    def _run():
        from apps.billing.services import sync_seat_quantity_by_id

        sync_seat_quantity_by_id(org_id)

    transaction.on_commit(_run)
