from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "read_at", "created")
    list_filter = ("created", "read_at")
    raw_id_fields = ("recipient", "organization", "actor", "target_content_type")
    readonly_fields = ("created", "modified")
