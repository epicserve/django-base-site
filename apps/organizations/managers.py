from django.apps import apps
from django.conf import settings
from django.db.models import Count, Q, QuerySet


class FilterByOrganizationMixin(QuerySet):
    def filter_by_org(self, request):
        return self.filter(organization=request.org.pk)


class OrganizationQuerySet(QuerySet):
    def get_user_org_count(self, user):
        org_member_model = apps.get_model("organizations.OrganizationMember")
        counts = org_member_model.objects.filter(user=user).aggregate(
            member_count=Count("pk"),
            owner_count=Count("pk", filter=Q(is_owner=True)),
        )
        return {
            "member_count": counts["member_count"] or 0,
            "owner_count": counts["owner_count"] or 0,
        }

    def non_members(self, org):
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        org_model = apps.get_model("organizations.Organization")
        return user_model.objects.filter(is_active=True).exclude(
            pk__in=org_model.objects.filter(organizationmember__organization=org).values_list("user_id", flat=True)
        )


class OrganizationMemberQuerySet(FilterByOrganizationMixin):
    pass


class OrganizationInviteQuerySet(FilterByOrganizationMixin):
    pass
