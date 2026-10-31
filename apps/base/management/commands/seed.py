"""
Seed the local database with known logins, organizations, teams and invites (idempotent).

Gives a developer, or an agent checking a UI change, a fixed set of accounts to
sign in as instead of clicking through signup and invites on every fresh
database. Every seeded user shares `SEED_PASSWORD`, so the command refuses to
run unless DEBUG is on. It also refuses while migrations are pending, because
the web container runs `migrate` on startup and `just seed` can race it.

Rerunning is safe. Each run creates whatever seeded rows are missing and
restores the seeded fields (names, roles, passwords) on the ones that exist.
It also removes MFA authenticators (TOTP, passkeys, recovery codes) from the
seeded users, so a seeded login always signs in with the password alone. Apart
from that it never deletes anything created by hand:

- Team members are only added, never removed.
- `is_primary` (on memberships and email addresses) is only set when a row is
  created and the user has no primary yet, because users change it in the app.
- An invite whose invitee has since joined the organization is skipped, since
  accepting an invite deletes it and creates the membership.

Invites are looked up by organization and email and created only when missing:
`OrganizationInvite.save()` runs `full_clean()`, whose duplicate check rejects
re-saving an existing invite, so `update_or_create` can't be used for them.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.teams.models import Team

# Deliberately well-known: the command only runs with DEBUG on, and agents need it to sign in.
SEED_PASSWORD = "dev-password"  # noqa: S105


@dataclass(frozen=True)
class SeedLogin:
    email: str
    first_name: str
    last_name: str
    role: str
    is_superuser: bool = False


LOGINS = (
    SeedLogin("admin@example.com", "Ada", "Admin", "Superuser and staff; owner of Globex", is_superuser=True),
    SeedLogin("owner@example.com", "Olivia", "Owner", "Owner of Acme; member of Globex"),
    SeedLogin("member@example.com", "Max", "Member", "Member of Acme (not an owner)"),
    SeedLogin("user@example.com", "Uma", "User", "No organization; pending invite to Acme"),
)

# Fillers give Acme a realistically long member list for layout and member-search checks.
FILLER_NAMES = (
    ("Alex", "Rivera"),
    ("Blake", "Chen"),
    ("Casey", "Okafor"),
    ("Dana", "Kowalski"),
    ("Eli", "Haddad"),
    ("Frankie", "Novak"),
    ("Gray", "Lindqvist"),
    ("Harper", "Mensah"),
    ("Indy", "Tanaka"),
    ("Jordan", "Alvarez"),
    ("Kai", "Brennan"),
    ("Logan", "Petrov"),
    ("Morgan", "Adeyemi"),
    ("Noel", "Fischer"),
    ("Parker", "Santos"),
    ("Quinn", "Moreau"),
    ("Reese", "Nakamura"),
    ("Sage", "Oduya"),
)
FILLERS = tuple(
    SeedLogin(f"{first}.{last}@example.com".lower(), first, last, "Member of Acme") for first, last in FILLER_NAMES
)

ORGANIZATIONS = (
    ("acme", "Acme Inc."),
    ("globex", "Globex Corporation"),
)

# (organization slug, user email, is_owner, is_primary)
MEMBERSHIPS = (
    ("globex", "admin@example.com", True, True),
    ("acme", "owner@example.com", True, True),
    ("globex", "owner@example.com", False, False),
    ("acme", "member@example.com", False, True),
    *(("acme", filler.email, False, True) for filler in FILLERS),
)

# (organization slug, team name, member emails)
TEAMS = (
    ("acme", "Engineering", ("owner@example.com", "member@example.com", *(f.email for f in FILLERS[:4]))),
    ("acme", "Design", ("member@example.com", *(f.email for f in FILLERS[4:7]))),
    ("globex", "Sales", ("admin@example.com", "owner@example.com")),
)

# (organization slug, sender email, invitee email, is_expired). An invitee with a seeded login is linked to it.
INVITES = (
    ("acme", "owner@example.com", "user@example.com", False),
    ("acme", "owner@example.com", "invitee@example.com", False),
    ("acme", "owner@example.com", "expired@example.com", True),
)


class Command(BaseCommand):
    help = "Create known dev logins, organizations, teams and invites (DEBUG only, idempotent)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(f"seed only runs with DEBUG on: every seeded login uses the password {SEED_PASSWORD!r}.")
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise CommandError("Migrations are still pending; retry once /api/app-context/ answers.")

        with transaction.atomic():
            users = self._seed_users()
            orgs = self._seed_organizations()
            self._seed_memberships(users, orgs)
            self._seed_teams(users, orgs)
            invites = self._seed_invites(users, orgs)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(users)} users, {len(orgs)} organizations, {len(TEAMS)} teams and {len(invites)} invites."
            )
        )
        self.stdout.write("")
        self.stdout.write(f'Sign in at {settings.SITE_URL}/accounts/login/ with the password "{SEED_PASSWORD}":')
        self.stdout.write("")
        width = max(len(login.email) for login in LOGINS)
        for login in LOGINS:
            self.stdout.write(f"    {login.email.ljust(width)}  {login.role}")
        self.stdout.write("")
        self.stdout.write(
            f"Acme also has {len(FILLERS)} filler members (e.g. {FILLERS[0].email}) with the same password."
        )
        if invites:
            # Seeded invites send no email, so print where to accept them.
            self.stdout.write("")
            self.stdout.write("Invites (no email is sent):")
            self.stdout.write("")
            width = max(len(invite.invitee_email) for invite in invites)
            for invite in invites:
                state = "expired" if invite.is_expired else "pending"
                url = f"{settings.SITE_URL}{invite.accept_invite_url}"
                self.stdout.write(f"    {invite.invitee_email.ljust(width)}  {state:<7}  {url}")

    def _seed_users(self) -> dict[str, User]:
        # Hash once: the default hasher is deliberately slow, and every seeded user shares the password.
        password = make_password(SEED_PASSWORD)
        users = {}
        for login in (*LOGINS, *FILLERS):
            user, _ = User.objects.update_or_create(
                username=login.email,
                defaults={
                    "email": login.email,
                    "first_name": login.first_name,
                    "last_name": login.last_name,
                    "is_active": True,
                    "is_staff": login.is_superuser,
                    "is_superuser": login.is_superuser,
                    "password": password,
                },
            )
            has_primary = EmailAddress.objects.filter(user=user, primary=True).exclude(email=login.email).exists()
            EmailAddress.objects.update_or_create(
                user=user,
                email=login.email,
                defaults={"verified": True},
                create_defaults={"verified": True, "primary": not has_primary},
            )
            users[login.email] = user
        # Enrolling TOTP or a passkey turns on MFA, which would stop a known password from being enough.
        removed, _ = Authenticator.objects.filter(user__in=users.values()).delete()
        if removed:
            self.stdout.write(f"Removed {removed} MFA authenticator(s) from seeded logins.")
        return users

    def _seed_organizations(self) -> dict[str, Organization]:
        orgs = {}
        for slug, name in ORGANIZATIONS:
            orgs[slug], _ = Organization.objects.update_or_create(slug=slug, defaults={"name": name})
        return orgs

    def _seed_memberships(self, users: dict[str, User], orgs: dict[str, Organization]) -> None:
        for slug, email, is_owner, is_primary in MEMBERSHIPS:
            user = users[email]
            has_primary = OrganizationMember.objects.filter(user=user, is_primary=True).exists()
            OrganizationMember.objects.update_or_create(
                organization=orgs[slug],
                user=user,
                defaults={"is_owner": is_owner},
                create_defaults={"is_owner": is_owner, "is_primary": is_primary and not has_primary},
            )

    def _seed_teams(self, users: dict[str, User], orgs: dict[str, Organization]) -> None:
        for slug, name, emails in TEAMS:
            team, _ = Team.objects.get_or_create(organization=orgs[slug], name=name)
            team.members.add(*(users[email] for email in emails))

    def _seed_invites(self, users: dict[str, User], orgs: dict[str, Organization]) -> list[OrganizationInvite]:
        invites = []
        now = timezone.now()
        for slug, sender_email, email, is_expired in INVITES:
            org = orgs[slug]
            if org.organizationmember_set.filter(user__email__iexact=email).exists():
                self.stdout.write(f"{email} is already a member of {org}, skipping their invite.")
                continue
            invite = OrganizationInvite.objects.filter(organization=org, invitee_email=email).first()
            if invite is None:
                invite = OrganizationInvite(
                    organization=org, sender=users[sender_email], invitee=users.get(email), invitee_email=email
                )
                invite.save()
            # `created` is auto_now_add, so backdate (or refresh) it with an update that skips save().
            created = now - timedelta(days=OrganizationInvite.expired_in_days + 1) if is_expired else now
            OrganizationInvite.objects.filter(pk=invite.pk).update(created=created)
            invite.created = created
            invites.append(invite)
        return invites
