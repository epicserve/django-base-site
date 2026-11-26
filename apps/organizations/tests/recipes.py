"""
Test data for organizations. Build organizations, members and invites with these instead of by hand.

They live in `apps.organizations.recipes`, because `manage.py seed` uses them too.
"""

from apps.organizations.recipes import make_invite, make_member, make_org

__all__ = ["make_invite", "make_member", "make_org"]
