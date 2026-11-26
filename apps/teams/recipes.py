"""
Build teams.

The tests use this (through `apps.teams.tests.recipes`), and so does `manage.py seed`, which passes `update=True`
(see `apps.accounts.recipes`).
"""

from collections.abc import Iterable
from itertools import count

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.teams.models import Team

_numbers = count(1)


def make_team(
    org: Organization, name: str | None = None, members: Iterable[User] = (), *, update: bool = False
) -> Team:
    """
    Make a team in `org` with `members`, who should already be members of the organization.

    With `update=True`, an existing team with that name gets `members` added; nobody is removed.
    """
    name = name or f"Team {next(_numbers)}"
    if update:
        team, _ = Team.objects.get_or_create(organization=org, name=name)
    else:
        team = Team.objects.create(organization=org, name=name)
    team.members.add(*members)
    return team
