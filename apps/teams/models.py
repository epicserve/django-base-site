from django.conf import settings
from django.db import models

from apps.base.mixins import TimeStampModelMixin
from apps.teams.managers import TeamQuerySet


class Team(TimeStampModelMixin, models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="teams")
    objects = TeamQuerySet.as_manager()

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):  # noqa: D105
        return self.name
