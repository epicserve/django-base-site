"""Test data for teams. `make_team` lives in `apps.teams.recipes`, because `manage.py seed` uses it too."""

from apps.teams.recipes import make_team

__all__ = ["make_team"]
