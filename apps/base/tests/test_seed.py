"""Tests for the `seed` management command behind `just seed`."""

from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import CommandError, call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, override_settings

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator

from apps.accounts.models import User
from apps.accounts.recipes import make_totp, make_user
from apps.base.management.commands import seed
from apps.base.management.commands.seed import DUNDER_MIFFLIN_CAST, FILLERS, LOGINS, PAWNEE_CAST, SEED_PASSWORD
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import api_sign_in
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import OrgRole
from apps.teams.models import Team

RUN_APP_SKILL = Path(settings.BASE_DIR) / ".agents" / "skills" / "run-app" / "SKILL.md"
SEEDED_MODELS = (User, EmailAddress, Organization, OrganizationMember, Team, OrganizationInvite)
SUPERUSER_USERNAME = "leslie"
SUPERUSER_EMAIL = "leslie.knope@pawnee.example"
SUPERUSER_PASSWORD = "waffles-and-binders"  # noqa: S105


def _seed():
    out = StringIO()
    call_command("seed", stdout=out)
    return out.getvalue()


def _counts():
    return {model.__name__: model.objects.count() for model in SEEDED_MODELS} | {
        "team members": Team.members.through.objects.count()
    }


# The DJANGO_SUPERUSER_* settings seed reads from .env.
@override_settings(
    DJANGO_SUPERUSER_USERNAME=SUPERUSER_USERNAME,
    DJANGO_SUPERUSER_EMAIL=SUPERUSER_EMAIL,
    DJANGO_SUPERUSER_PASSWORD=SUPERUSER_PASSWORD,
)
class SeedTest(BaseTest):
    """Lets seed use the test database's host, from before `setUpTestData` runs."""

    @classmethod
    def setUpClass(cls):
        # seed refuses hosts it doesn't know are local, and CI's test database is on the Docker host (172.17.0.1).
        local_hosts = seed.LOCAL_DB_HOSTS | {connections["default"].settings_dict["HOST"]}
        cls.enterClassContext(mock.patch.object(seed, "LOCAL_DB_HOSTS", local_hosts))
        super().setUpClass()


@override_settings(DEBUG=True)
class TestSeedDevGuards(SeedTest):
    def test_refuses_without_debug(self):
        with self.settings(DEBUG=False), pytest.raises(CommandError, match="DEBUG"):
            _seed()
        assert not User.objects.exists()

    def test_refuses_with_pending_migrations(self):
        with (
            mock.patch.object(MigrationExecutor, "migration_plan", return_value=[("accounts", False)]),
            pytest.raises(CommandError, match="Migrations are still pending"),
        ):
            _seed()
        assert not User.objects.exists()

    def test_refuses_a_remote_database(self):
        # The guard runs before the first query, so changing the host of the open test connection is harmless.
        with (
            mock.patch.dict(connections["default"].settings_dict, {"HOST": "db.production.example"}),
            pytest.raises(CommandError, match="local database, not 'db.production.example'"),
        ):
            _seed()
        assert not User.objects.exists()

    def test_refuses_without_superuser_credentials(self):
        for name in seed.SUPERUSER_SETTINGS:
            with self.subTest(name=name):
                with (
                    self.settings(**{name: ""}),
                    pytest.raises(CommandError, match="DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL"),
                ):
                    _seed()
                assert not User.objects.exists()

    def test_refuses_a_superuser_email_another_user_has(self):
        # Only the user's own email matches; their EmailAddress is another one.
        ann = make_user("ann@example.com", username="ann.perkins")
        User.objects.filter(pk=ann.pk).update(email=SUPERUSER_EMAIL)
        with pytest.raises(CommandError, match="already belongs to the user 'ann.perkins'"):
            _seed()
        assert not User.objects.filter(username=SUPERUSER_USERNAME).exists()


@override_settings(DEBUG=True)
class TestSeedDevData(SeedTest):
    @classmethod
    def setUpTestData(cls):
        cls.output = _seed()

    def test_creates_logins_with_verified_primary_email(self):
        for login in (*LOGINS, *FILLERS):
            user = User.objects.get(username=login.email)
            assert user.check_password(SEED_PASSWORD)
            assert EmailAddress.objects.filter(user=user, email=login.email, verified=True, primary=True).exists()
            assert not user.is_staff
            assert not user.is_superuser
        assert User.objects.get(email="owner@example.com").get_full_name() == "Michael Scott"

    def test_superuser_comes_from_env(self):
        superuser = User.objects.get(username=SUPERUSER_USERNAME)
        assert superuser.email == SUPERUSER_EMAIL
        assert (superuser.get_full_name(), superuser.is_superuser, superuser.is_staff) == ("Leslie Knope", True, True)
        assert superuser.check_password(SUPERUSER_PASSWORD)
        assert EmailAddress.objects.filter(user=superuser, email=SUPERUSER_EMAIL, verified=True, primary=True).exists()

    def test_memberships(self):
        dunder_mifflin = Organization.objects.get(slug="dunder-mifflin")
        pawnee = Organization.objects.get(slug="pawnee-parks")
        assert dunder_mifflin.organizationmember_set.count() == 20
        assert set(dunder_mifflin.members.values_list("email", flat=True)) == {
            "owner@example.com",
            "member@example.com",
            *(member.email for member in DUNDER_MIFFLIN_CAST),
        }
        dunder_mifflin_owners = dunder_mifflin.organizationmember_set.filter(role=OrgRole.OWNER)
        assert list(dunder_mifflin_owners.values_list("user__email", flat=True)) == ["owner@example.com"]
        assert set(pawnee.members.values_list("username", flat=True)) == {
            SUPERUSER_USERNAME,
            "owner@example.com",
            *(member.email for member in PAWNEE_CAST),
        }
        pawnee_owners = pawnee.organizationmember_set.filter(role=OrgRole.OWNER)
        assert list(pawnee_owners.values_list("user__username", flat=True)) == [SUPERUSER_USERNAME]
        owner_primary = OrganizationMember.objects.filter(user__email="owner@example.com", is_primary=True)
        assert list(owner_primary.values_list("organization__slug", flat=True)) == ["dunder-mifflin"]
        assert not OrganizationMember.objects.filter(user__email="user@example.com").exists()

    def test_teams_only_contain_org_members(self):
        assert Team.objects.count() == 3
        for team in Team.objects.all():
            assert team.members.exists()
            assert not team.members.exclude(pk__in=team.organization.members).exists()

    def test_invites(self):
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

    def test_prints_the_logins_and_invite_urls(self):
        assert SEED_PASSWORD in self.output
        for login in LOGINS:
            assert login.email in self.output
        assert SUPERUSER_EMAIL in self.output
        # The superuser's password may come from 1Password, so it stays out of the terminal.
        assert "DJANGO_SUPERUSER_PASSWORD from .env" in self.output
        assert SUPERUSER_PASSWORD not in self.output
        # Seeded invites send no email, so the output is the only place to find their accept URLs.
        for invite in OrganizationInvite.objects.all():
            assert invite.accept_invite_url in self.output


@override_settings(DEBUG=True)
class TestSeedDevRerun(SeedTest):
    @classmethod
    def setUpTestData(cls):
        _seed()

    def test_second_run_changes_nothing(self):
        before = _counts()
        _seed()
        assert _counts() == before

    def test_restores_seeded_fields_and_keeps_hand_made_changes(self):
        # Each change touches different rows, so one rerun checks them all.
        member = User.objects.get(email="member@example.com")
        member.set_password("something-else")
        member.save()

        User.objects.filter(username=SUPERUSER_USERNAME).update(is_superuser=False, is_staff=False, first_name="Knope")
        superuser = User.objects.get(username=SUPERUSER_USERNAME)
        superuser.set_password("something-else")
        superuser.save()

        # Accepting an invite creates the membership and deletes the invite (see `accept_invite` in the API).
        invite = OrganizationInvite.objects.get(invitee_email="user@example.com")
        OrganizationMember.objects.create(organization=invite.organization, user=invite.invitee)
        invite.delete()

        sales = Team.objects.get(name="Sales")
        accountant = User.objects.get(email="kevin.malone@dundermifflin.example")
        sales.members.add(accountant)
        # Users pick their primary org in the app; the seed must not move it back.
        OrganizationMember.objects.filter(user__email="owner@example.com").update(is_primary=False)
        OrganizationMember.objects.filter(user__email="owner@example.com", organization__slug="pawnee-parks").update(
            is_primary=True
        )

        output = _seed()

        with self.subTest("resets a changed password"):
            member.refresh_from_db()
            assert member.check_password(SEED_PASSWORD)

        with self.subTest("restores the superuser"):
            superuser.refresh_from_db()
            assert (superuser.get_full_name(), superuser.is_superuser, superuser.is_staff) == (
                "Leslie Knope",
                True,
                True,
            )
            assert superuser.check_password(SUPERUSER_PASSWORD)

        with self.subTest("skips an accepted invite"):
            assert "user@example.com is already a member of Dunder Mifflin Paper Company, Inc., skipping" in output
            assert not OrganizationInvite.objects.filter(invitee_email="user@example.com").exists()
            assert OrganizationMember.objects.filter(
                user__email="user@example.com", organization__slug="dunder-mifflin"
            ).exists()

        with self.subTest("keeps hand-made changes"):
            assert sales.members.filter(pk=accountant.pk).exists()
            owner_primary = OrganizationMember.objects.filter(user__email="owner@example.com", is_primary=True)
            assert list(owner_primary.values_list("organization__slug", flat=True)) == ["pawnee-parks"]


class TestSeedDevLogin(SeedTest):
    """Signing in as the seeded logins. Only the command needs DEBUG; with it on, requests try to render the toolbar."""

    @classmethod
    def setUpTestData(cls):
        with override_settings(DEBUG=True):
            _seed()

    def test_seeded_login_can_sign_in(self):
        for login in LOGINS:
            with self.subTest(email=login.email):
                client = Client()
                resp = api_sign_in(client, login.email, SEED_PASSWORD)
                assert resp.status_code == 200, resp.content
                assert client.session.get("_auth_user_id") == str(User.objects.get(email=login.email).pk)

    def test_superuser_signs_in_with_the_env_password(self):
        assert api_sign_in(self.client, SUPERUSER_EMAIL, SEED_PASSWORD).status_code == 400
        resp = api_sign_in(self.client, SUPERUSER_EMAIL, SUPERUSER_PASSWORD)
        assert resp.status_code == 200, resp.content

    def test_rerun_removes_mfa_so_the_password_is_enough(self):
        # Enrolling TOTP (or a passkey) while testing MFA would otherwise leave the login asking for a code.
        passwords = {"owner@example.com": SEED_PASSWORD, SUPERUSER_EMAIL: SUPERUSER_PASSWORD}
        for email, password in passwords.items():
            make_totp(User.objects.get(email=email))
            assert api_sign_in(Client(), email, password).status_code == 401

        with self.settings(DEBUG=True):
            _seed()

        for email, password in passwords.items():
            with self.subTest(email=email):
                assert not Authenticator.objects.filter(user__email=email).exists()
                assert api_sign_in(Client(), email, password).status_code == 200


class TestRunAppSkill:
    def test_skill_lists_every_seeded_login(self):
        # The run-app skill tells agents which login to use; keep it in step with the command.
        skill = RUN_APP_SKILL.read_text()
        assert SEED_PASSWORD in skill
        for login in LOGINS:
            assert login.email in skill
        assert "DJANGO_SUPERUSER_EMAIL" in skill
        assert "DJANGO_SUPERUSER_PASSWORD" in skill
