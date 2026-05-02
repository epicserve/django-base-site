from django.shortcuts import get_object_or_404

from ninja import Query, Router, Status
from ninja.pagination import paginate

from apps.base.ninja_pagination import LegacyPagination
from apps.base.permissions import require_org_owner
from apps.organizations.models import OrganizationMember
from apps.teams.models import Team
from apps.teams.schemas import TeamIn, TeamOut, TeamPatchIn

router = Router(tags=["teams"])


def _team_qs(request):
    return Team.objects.filter_by_org(request).prefetch_related("members").order_by("name")


def _validate_members(member_ids: list[int], org) -> list[int]:
    if not member_ids:
        return []
    org_user_ids = set(OrganizationMember.objects.filter(organization=org).values_list("user_id", flat=True))
    invalid = [pk for pk in member_ids if pk not in org_user_ids]
    if invalid:
        from django.core.exceptions import ValidationError

        raise ValidationError({"members": [f"User id {pk} is not a member of this organization." for pk in invalid]})
    return member_ids


@router.get("/", response=list[TeamOut])
@paginate(LegacyPagination)
def list_teams(request, q: str | None = Query(None)):
    require_org_owner(request)
    qs = _team_qs(request)
    if q:
        qs = qs.filter(name__icontains=q)
    return qs


@router.post("/", response={201: TeamOut})
def create_team(request, payload: TeamIn):
    org = require_org_owner(request)
    member_ids = _validate_members(payload.members, org)
    team = Team.objects.create(organization=org, name=payload.name)
    if member_ids:
        team.members.set(member_ids)
    return Status(201, team)


@router.get("/{team_id}/", response=TeamOut)
def get_team(request, team_id: int):
    require_org_owner(request)
    return get_object_or_404(_team_qs(request), pk=team_id)


@router.patch("/{team_id}/", response=TeamOut)
def patch_team(request, team_id: int, payload: TeamPatchIn):
    org = require_org_owner(request)
    team = get_object_or_404(_team_qs(request), pk=team_id)
    if payload.name is not None:
        team.name = payload.name
        team.save(update_fields=["name", "modified"])
    if payload.members is not None:
        member_ids = _validate_members(payload.members, org)
        team.members.set(member_ids)
    return team


@router.delete("/{team_id}/", response={204: None})
def delete_team(request, team_id: int):
    require_org_owner(request)
    team = get_object_or_404(_team_qs(request), pk=team_id)
    team.delete()
    return Status(204, None)
