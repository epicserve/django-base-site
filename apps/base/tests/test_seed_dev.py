"""Tests for the `seed_dev` management command behind `just seed`."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings as django_settings
from django.core.management import CommandError, call_command
from django.db.migrations.executor import MigrationExecutor

import pytest
from allauth.account.models import EmailAddress

from apps.accounts.models import User
from apps.base.management.commands.seed_dev import FILLERS, LOGINS, SEED_PASSWORD
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.teams.models import Team

RUN_APP_SKILL = Path(django_settings.BASE_DIR) / ".agents" / "skills" / "run-app" / "SKILL.md"
SEEDED_MODELS = (User, EmailAddress, Organization, OrganizationMember, Team, OrganizationInvite)


def _seed():
    out = StringIO()
    call_command("seed_dev", stdout=out)
    return out.getvalue()


def _counts():
    return {model.__name__: model.objects.count() for model in SEEDED_MODELS} | {
        "team members": Team.members.through.objects.count()
    }


@pytest.fixture()
def debug(settings):
    settings.DEBUG = True


@pytest.mark.django_db
class TestSeedDevGuards:
    def test_refuses_without_debug(self, settings):
        settings.DEBUG = False
        with pytest.raises(CommandError, match="DEBUG"):
            _seed()
        assert not User.objects.exists()

    @pytest.mark.usefixtures("debug")
    def test_refuses_with_pending_migrations(self):
        with (
            patch.object(MigrationExecutor, "migration_plan", return_value=[("accounts", False)]),
            pytest.raises(CommandError, match="Migrations are still pending"),
        ):
            _seed()
        assert not User.objects.exists()


@pytest.mark.django_db
@pytest.mark.usefixtures("debug")
class TestSeedDevData:
    def test_creates_logins_with_verified_primary_email(self):
        _seed()
        for login in (*LOGINS, *FILLERS):
            user = User.objects.get(username=login.email)
            assert user.check_password(SEED_PASSWORD)
            assert EmailAddress.objects.filter(user=user, email=login.email, verified=True, primary=True).exists()
        admin = User.objects.get(email="admin@example.com")
        assert admin.is_superuser
        assert admin.is_staff
        assert not User.objects.get(email="owner@example.com").is_staff

    def test_memberships(self):
        _seed()
        acme = Organization.objects.get(slug="acme")
        globex = Organization.objects.get(slug="globex")
        assert acme.organizationmember_set.count() == 20
        assert list(acme.owners.values_list("email", flat=True)) == ["owner@example.com"]
        assert set(globex.members.values_list("email", flat=True)) == {"admin@example.com", "owner@example.com"}
        assert list(globex.owners.values_list("email", flat=True)) == ["admin@example.com"]
        owner_primary = OrganizationMember.objects.filter(user__email="owner@example.com", is_primary=True)
        assert list(owner_primary.values_list("organization__slug", flat=True)) == ["acme"]
        assert not OrganizationMember.objects.filter(user__email="user@example.com").exists()

    def test_teams_only_contain_org_members(self):
        _seed()
        assert Team.objects.count() == 3
        for team in Team.objects.all():
            assert team.members.exists()
            assert not team.members.exclude(pk__in=team.organization.members).exists()

    def test_invites(self):
        _seed()
        invites = {invite.invitee_email: invite for invite in OrganizationInvite.objects.all()}
        assert set(invites) == {"user@example.com", "invitee@example.com", "expired@example.com"}
        assert invites["user@example.com"].invitee == User.objects.get(email="user@example.com")
        assert invites["invitee@example.com"].invitee is None
        assert invites["expired@example.com"].is_expired
        assert not invites["user@example.com"].is_expired
        assert not invites["invitee@example.com"].is_expired

    def test_prints_the_logins_and_invite_urls(self):
        output = _seed()
        assert SEED_PASSWORD in output
        for login in LOGINS:
            assert login.email in output
        # Seeded invites send no email, so the output is the only place to find their accept URLs.
        for invite in OrganizationInvite.objects.all():
            assert invite.accept_invite_url in output


@pytest.mark.django_db
@pytest.mark.usefixtures("debug")
class TestSeedDevRerun:
    def test_second_run_changes_nothing(self):
        _seed()
        before = _counts()
        _seed()
        assert _counts() == before

    def test_resets_a_changed_password(self):
        _seed()
        user = User.objects.get(email="member@example.com")
        user.set_password("something-else")
        user.save()
        _seed()
        user.refresh_from_db()
        assert user.check_password(SEED_PASSWORD)

    def test_skips_an_accepted_invite(self):
        _seed()
        # Accepting an invite creates the membership and deletes the invite (see `accept_invite` in the API).
        invite = OrganizationInvite.objects.get(invitee_email="user@example.com")
        OrganizationMember.objects.create(organization=invite.organization, user=invite.invitee)
        invite.delete()

        output = _seed()

        assert "user@example.com is already a member of Acme Inc., skipping" in output
        assert not OrganizationInvite.objects.filter(invitee_email="user@example.com").exists()
        assert OrganizationMember.objects.filter(user__email="user@example.com", organization__slug="acme").exists()

    def test_keeps_hand_made_changes(self):
        _seed()
        engineering = Team.objects.get(name="Engineering")
        designer = User.objects.get(email=FILLERS[-1].email)
        engineering.members.add(designer)
        # Users pick their primary org in the app; the seed must not move it back.
        OrganizationMember.objects.filter(user__email="owner@example.com").update(is_primary=False)
        OrganizationMember.objects.filter(user__email="owner@example.com", organization__slug="globex").update(
            is_primary=True
        )

        _seed()

        assert engineering.members.filter(pk=designer.pk).exists()
        owner_primary = OrganizationMember.objects.filter(user__email="owner@example.com", is_primary=True)
        assert list(owner_primary.values_list("organization__slug", flat=True)) == ["globex"]


@pytest.mark.django_db
class TestSeedDevLogin:
    @pytest.fixture(autouse=True)
    def _seeded(self, settings):
        settings.DEBUG = True
        _seed()
        # Only the command needs DEBUG; with it on, requests try to render the debug toolbar.
        settings.DEBUG = False
        # The test runner defaults to ModelBackend (username-based); sign in by email the way the SPA does.
        settings.AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]

    @pytest.mark.parametrize("email", [login.email for login in LOGINS])
    def test_seeded_login_can_sign_in(self, client, email):
        resp = client.post(
            "/_allauth/browser/v1/auth/login",
            data={"email": email, "password": SEED_PASSWORD},
            content_type="application/json",
        )
        assert resp.status_code == 200, resp.content
        assert client.session.get("_auth_user_id") == str(User.objects.get(email=email).pk)


class TestRunAppSkill:
    def test_skill_lists_every_seeded_login(self):
        # The run-app skill tells agents which login to use; keep it in step with the command.
        skill = RUN_APP_SKILL.read_text()
        assert SEED_PASSWORD in skill
        for login in LOGINS:
            assert login.email in skill
