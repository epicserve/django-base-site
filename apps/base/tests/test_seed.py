"""Tests for the `seed` management command behind `just seed`."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings as django_settings
from django.core.management import CommandError, call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator

from apps.accounts.models import User
from apps.base.management.commands import seed
from apps.base.management.commands.seed import DUNDER_MIFFLIN_CAST, FILLERS, LOGINS, PAWNEE_CAST, SEED_PASSWORD
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.teams.models import Team

RUN_APP_SKILL = Path(django_settings.BASE_DIR) / ".agents" / "skills" / "run-app" / "SKILL.md"
SEEDED_MODELS = (User, EmailAddress, Organization, OrganizationMember, Team, OrganizationInvite)
SUPERUSER_PASSWORD = "waffles-and-binders"  # noqa: S105


def _seed():
    out = StringIO()
    call_command("seed", stdout=out)
    return out.getvalue()


def _counts():
    return {model.__name__: model.objects.count() for model in SEEDED_MODELS} | {
        "team members": Team.members.through.objects.count()
    }


@pytest.fixture(autouse=True)
def superuser_credentials(settings, monkeypatch):
    """Set the DJANGO_SUPERUSER_* settings seed reads from .env, and let seed use the test database's host."""
    credentials = {"username": "leslie", "email": "leslie.knope@pawnee.example", "password": SUPERUSER_PASSWORD}
    for field, value in credentials.items():
        setattr(settings, f"DJANGO_SUPERUSER_{field.upper()}", value)
    # seed refuses hosts it doesn't know are local, and CI's test database is on the Docker host (172.17.0.1).
    monkeypatch.setattr(seed, "LOCAL_DB_HOSTS", seed.LOCAL_DB_HOSTS | {connections["default"].settings_dict["HOST"]})
    return credentials


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

    @pytest.mark.usefixtures("debug")
    def test_refuses_a_remote_database(self, monkeypatch):
        # The guard runs before the first query, so changing the host of the open test connection is harmless.
        monkeypatch.setitem(connections["default"].settings_dict, "HOST", "db.production.example")
        with pytest.raises(CommandError, match="local database, not 'db.production.example'"):
            _seed()
        assert not User.objects.exists()

    @pytest.mark.usefixtures("debug")
    @pytest.mark.parametrize("name", seed.SUPERUSER_SETTINGS)
    def test_refuses_without_superuser_credentials(self, settings, name):
        setattr(settings, name, "")
        with pytest.raises(CommandError, match="DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL"):
            _seed()
        assert not User.objects.exists()

    @pytest.mark.usefixtures("debug")
    def test_refuses_a_superuser_email_another_user_has(self, superuser_credentials):
        User.objects.create_user(username="ann.perkins", email=superuser_credentials["email"])
        with pytest.raises(CommandError, match="already belongs to the user 'ann.perkins'"):
            _seed()
        assert not User.objects.filter(username="leslie").exists()


@pytest.mark.django_db
@pytest.mark.usefixtures("debug")
class TestSeedDevData:
    def test_creates_logins_with_verified_primary_email(self):
        _seed()
        for login in (*LOGINS, *FILLERS):
            user = User.objects.get(username=login.email)
            assert user.check_password(SEED_PASSWORD)
            assert EmailAddress.objects.filter(user=user, email=login.email, verified=True, primary=True).exists()
            assert not user.is_staff
            assert not user.is_superuser
        assert User.objects.get(email="owner@example.com").get_full_name() == "Michael Scott"

    def test_superuser_comes_from_env(self, superuser_credentials):
        _seed()
        superuser = User.objects.get(username="leslie")
        assert superuser.email == superuser_credentials["email"]
        assert (superuser.get_full_name(), superuser.is_superuser, superuser.is_staff) == ("Leslie Knope", True, True)
        assert superuser.check_password(SUPERUSER_PASSWORD)
        assert EmailAddress.objects.filter(
            user=superuser, email=superuser_credentials["email"], verified=True, primary=True
        ).exists()

    def test_memberships(self):
        _seed()
        dunder_mifflin = Organization.objects.get(slug="dunder-mifflin")
        pawnee = Organization.objects.get(slug="pawnee-parks")
        assert dunder_mifflin.organizationmember_set.count() == 20
        assert set(dunder_mifflin.members.values_list("email", flat=True)) == {
            "owner@example.com",
            "member@example.com",
            *(member.email for member in DUNDER_MIFFLIN_CAST),
        }
        assert list(dunder_mifflin.owners.values_list("email", flat=True)) == ["owner@example.com"]
        assert set(pawnee.members.values_list("username", flat=True)) == {
            "leslie",
            "owner@example.com",
            *(member.email for member in PAWNEE_CAST),
        }
        assert list(pawnee.owners.values_list("username", flat=True)) == ["leslie"]
        owner_primary = OrganizationMember.objects.filter(user__email="owner@example.com", is_primary=True)
        assert list(owner_primary.values_list("organization__slug", flat=True)) == ["dunder-mifflin"]
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
        assert set(invites) == {
            "user@example.com",
            "holly.flax@dundermifflin.example",
            "todd.packer@dundermifflin.example",
        }
        assert invites["user@example.com"].invitee == User.objects.get(email="user@example.com")
        assert invites["holly.flax@dundermifflin.example"].invitee is None
        assert invites["todd.packer@dundermifflin.example"].is_expired
        assert not invites["user@example.com"].is_expired
        assert not invites["holly.flax@dundermifflin.example"].is_expired

    def test_prints_the_logins_and_invite_urls(self, superuser_credentials):
        output = _seed()
        assert SEED_PASSWORD in output
        for login in LOGINS:
            assert login.email in output
        assert superuser_credentials["email"] in output
        # The superuser's password may come from 1Password, so it stays out of the terminal.
        assert "DJANGO_SUPERUSER_PASSWORD from .env" in output
        assert SUPERUSER_PASSWORD not in output
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

    def test_restores_the_superuser(self):
        _seed()
        User.objects.filter(username="leslie").update(is_superuser=False, is_staff=False, first_name="Knope")
        superuser = User.objects.get(username="leslie")
        superuser.set_password("something-else")
        superuser.save()

        _seed()

        superuser.refresh_from_db()
        assert (superuser.get_full_name(), superuser.is_superuser, superuser.is_staff) == ("Leslie Knope", True, True)
        assert superuser.check_password(SUPERUSER_PASSWORD)

    def test_skips_an_accepted_invite(self):
        _seed()
        # Accepting an invite creates the membership and deletes the invite (see `accept_invite` in the API).
        invite = OrganizationInvite.objects.get(invitee_email="user@example.com")
        OrganizationMember.objects.create(organization=invite.organization, user=invite.invitee)
        invite.delete()

        output = _seed()

        assert "user@example.com is already a member of Dunder Mifflin Paper Company, Inc., skipping" in output
        assert not OrganizationInvite.objects.filter(invitee_email="user@example.com").exists()
        assert OrganizationMember.objects.filter(
            user__email="user@example.com", organization__slug="dunder-mifflin"
        ).exists()

    def test_keeps_hand_made_changes(self):
        _seed()
        sales = Team.objects.get(name="Sales")
        accountant = User.objects.get(email="kevin.malone@dundermifflin.example")
        sales.members.add(accountant)
        # Users pick their primary org in the app; the seed must not move it back.
        OrganizationMember.objects.filter(user__email="owner@example.com").update(is_primary=False)
        OrganizationMember.objects.filter(user__email="owner@example.com", organization__slug="pawnee-parks").update(
            is_primary=True
        )

        _seed()

        assert sales.members.filter(pk=accountant.pk).exists()
        owner_primary = OrganizationMember.objects.filter(user__email="owner@example.com", is_primary=True)
        assert list(owner_primary.values_list("organization__slug", flat=True)) == ["pawnee-parks"]


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

    @staticmethod
    def _sign_in(client, email, password=SEED_PASSWORD):
        return client.post(
            "/_allauth/browser/v1/auth/login",
            data={"email": email, "password": password},
            content_type="application/json",
        )

    @pytest.mark.parametrize("email", [login.email for login in LOGINS])
    def test_seeded_login_can_sign_in(self, client, email):
        resp = self._sign_in(client, email)
        assert resp.status_code == 200, resp.content
        assert client.session.get("_auth_user_id") == str(User.objects.get(email=email).pk)

    def test_superuser_signs_in_with_the_env_password(self, client, superuser_credentials):
        assert self._sign_in(client, superuser_credentials["email"]).status_code == 400
        resp = self._sign_in(client, superuser_credentials["email"], SUPERUSER_PASSWORD)
        assert resp.status_code == 200, resp.content

    @pytest.mark.parametrize(
        ("username", "password"), [("owner@example.com", SEED_PASSWORD), ("leslie", SUPERUSER_PASSWORD)]
    )
    def test_rerun_removes_mfa_so_the_password_is_enough(self, client, settings, username, password):
        # Enrolling TOTP (or a passkey) while testing MFA would otherwise leave the login asking for a code.
        user = User.objects.get(username=username)
        Authenticator.objects.create(user=user, type=Authenticator.Type.TOTP, data={"secret": "JBSWY3DPEHPK3PXP"})
        Authenticator.objects.create(user=user, type=Authenticator.Type.RECOVERY_CODES, data={"seed": "00"})
        assert self._sign_in(client, user.email, password).status_code == 401

        settings.DEBUG = True
        _seed()
        settings.DEBUG = False

        assert not Authenticator.objects.filter(user=user).exists()
        assert self._sign_in(client, user.email, password).status_code == 200


class TestRunAppSkill:
    def test_skill_lists_every_seeded_login(self):
        # The run-app skill tells agents which login to use; keep it in step with the command.
        skill = RUN_APP_SKILL.read_text()
        assert SEED_PASSWORD in skill
        for login in LOGINS:
            assert login.email in skill
        assert "DJANGO_SUPERUSER_EMAIL" in skill
        assert "DJANGO_SUPERUSER_PASSWORD" in skill
