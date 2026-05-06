from django.db import models


class NotificationQuerySet(models.QuerySet):
    def filter_by_org(self, request):
        org = request.org
        if org.id is not None:
            return self.filter(recipient=request.user, organization_id=org.id)
        return self.filter(recipient=request.user, organization__isnull=True)
