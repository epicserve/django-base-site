import hashlib
import urllib.parse

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def gravatar_image_url(context, email, default="mm", size=20):
    email_bytes = email.encode("utf-8").strip().lower()
    hashed = hashlib.md5(email_bytes).hexdigest()  # noqa: S324
    params = urllib.parse.urlencode({"d": default, "s": size})
    return f"https://secure.gravatar.com/avatar/{hashed}?{params}"
