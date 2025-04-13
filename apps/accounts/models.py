import hashlib
import urllib.parse

from django.contrib.auth.models import AbstractUser
from django.utils.safestring import mark_safe


class User(AbstractUser):
    def _get_gravatar_url(self, size: int = 40):
        # See the documentation for the default parameter: https://docs.gravatar.com/api/avatars/images/
        default = "mp"
        hashed_email = hashlib.md5(self.email.lower().encode()).hexdigest()  # noqa: S324
        params = urllib.parse.urlencode({"d": default, "s": str(size)})
        return f"https://www.gravatar.com/avatar/{hashed_email}?{params}"

    @property
    def gravatar(self):
        size = 40
        url = self._get_gravatar_url(size=size)
        return mark_safe(f'<img src="{url}" height="{size}" width="{size}" class="rounded-5">')  # noqa: S308
