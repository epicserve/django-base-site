from django.apps import apps
from django.conf import settings
from django.db.models import QuerySet


class FilterByOrganizationMixin(QuerySet):
    def filter_by_org(self, request):
        return self.filter(organization=request.org.pk)


class OrganizationQuerySet(QuerySet):
    def get_user_org_count(self, user):
        member_count = 0
        owner_count = 0
        org_member_model = apps.get_model("organizations.OrganizationMember")
        for org_member in org_member_model.objects.filter(
            pk__in=self.prefetch_related("organizationmember")
            .filter(organizationmember__user=user)
            .values_list("organizationmember__pk", flat=True)
        ):
            member_count += 1
            if org_member.is_owner is True:
                owner_count += 1

        return {
            "member_count": member_count,
            "owner_count": owner_count,
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
