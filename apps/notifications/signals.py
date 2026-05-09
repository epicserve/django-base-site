from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete

from apps.notifications.models import Notification


def _delete_notifications_for_target(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(sender)
    Notification.objects.filter(target_content_type=ct, target_object_id=instance.pk).delete()


def connect_target_receivers():
    """
    Connect post_delete cleanup for each model listed in settings.NOTIFICATIONS_TARGET_MODELS.

    Notification.target is a GenericForeignKey, so the database has no FK CASCADE
    to clean up rows whose target row was deleted. This receiver provides that
    cascade in application code, scoped per-model so unrelated deletes don't pay
    the cost.
    """
    for label in getattr(settings, "NOTIFICATIONS_TARGET_MODELS", ()):
        model = django_apps.get_model(label)
        post_delete.connect(
            _delete_notifications_for_target,
            sender=model,
            dispatch_uid=f"notifications.cascade.{label}",
        )
