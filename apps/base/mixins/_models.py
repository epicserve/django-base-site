from django.db import models


class TimeStampModelMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseListModelMixin(TimeStampModelMixin):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
