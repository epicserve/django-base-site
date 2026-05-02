import logging
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

logger = logging.getLogger(__name__)


def avatar_original_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"avatars/originals/{instance.pk}/{uuid4().hex}.{ext}"


def avatar_thumbnail_path(instance, filename):
    return f"avatars/thumbnails/{instance.pk}/{uuid4().hex}.jpg"


class User(AbstractUser):
    timezone = models.CharField(max_length=63, default="America/Chicago")
    avatar_original = models.ImageField(upload_to=avatar_original_path, blank=True)
    avatar_thumbnail = models.ImageField(upload_to=avatar_thumbnail_path, blank=True)
    avatar_crop_data = models.JSONField(blank=True, null=True)

    def clean(self):
        super().clean()
        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except (ZoneInfoNotFoundError, KeyError) as err:
                raise ValidationError({"timezone": f"Invalid timezone: {self.timezone}"}) from err

    @property
    def avatar_url(self):
        if self.avatar_thumbnail:
            return self.avatar_thumbnail.url
        return None
