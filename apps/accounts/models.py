import hashlib
import logging
import urllib.parse
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

TIMEZONE_CHOICES = sorted([(tz, tz) for tz in available_timezones()])


def avatar_original_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"avatars/originals/{instance.pk}/{uuid4().hex}.{ext}"


def avatar_thumbnail_path(instance, filename):
    return f"avatars/thumbnails/{instance.pk}/{uuid4().hex}.jpg"


class User(AbstractUser):
    timezone = models.CharField(max_length=63, default="America/Chicago", choices=TIMEZONE_CHOICES)
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

    def _get_gravatar_url(self, size: int = 40):
        # See the documentation for the default parameter: https://docs.gravatar.com/api/avatars/images/
        default = "mp"
        hashed_email = hashlib.md5(self.email.lower().encode()).hexdigest()  # noqa: S324
        params = urllib.parse.urlencode({"d": default, "s": str(size)})
        return f"https://www.gravatar.com/avatar/{hashed_email}?{params}"

    @property
    def avatar_url(self):
        if self.avatar_thumbnail:
            return self.avatar_thumbnail.url
        return self._get_gravatar_url(size=256)

    @property
    def gravatar(self):
        size = 40
        url = self._get_gravatar_url(size=size)
        return mark_safe(f'<img src="{url}" height="{size}" width="{size}" class="rounded-5">')  # noqa: S308
