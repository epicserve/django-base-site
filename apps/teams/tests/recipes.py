"""Test data for teams."""

from collections.abc import Iterable
from itertools import count

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.teams.models import Team

_numbers = count(1)


def make_team(org: Organization, name: str | None = None, members: Iterable[User] = ()) -> Team:
    """Make a team in `org` with `members`, who should already be members of the organization."""
    team = Team.objects.create(organization=org, name=name or f"Team {next(_numbers)}")
    team.members.add(*members)
    return team
