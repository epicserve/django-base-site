"""
Seed the local database with known logins, organizations, teams and invites (idempotent).

Gives a developer, or an agent checking a UI change, a fixed set of accounts to
sign in as instead of clicking through signup and invites on every fresh
database. Every seeded user except the superuser shares `SEED_PASSWORD`, so the
command refuses to run unless DEBUG is on, and against any database that isn't
local (`LOCAL_DB_HOSTS`). It also refuses while migrations are pending, because
the web container runs `migrate` on startup and `just seed` can race it.

The superuser is the account in DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD
(.env), the same one `just create_superuser` makes, so its password is never
the well-known one. `just create_env` fills those from 1Password, or with
fallbacks (see .env.toml).

The cast comes from The Office (Dunder Mifflin) and Parks and Recreation
(Pawnee). The logins agents and docs refer to keep role emails such as
`owner@example.com`; everyone else gets an email on a reserved `.example`
domain, so nothing seeded can ever reach a real inbox.

Rerunning is safe. Each run creates whatever seeded rows are missing and
restores the seeded fields (names, roles, passwords, the superuser's flags) on
the ones that exist. It also removes MFA authenticators (TOTP, passkeys,
recovery codes) from the seeded users, so a seeded login always signs in with
the password alone. Apart
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
from django.db.models import Q
from django.utils import timezone

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.teams.models import Team

# Deliberately well-known: the command only runs with DEBUG on against a local database, and agents need it to
# sign in. The superuser doesn't use it.
SEED_PASSWORD = "dev-password"  # noqa: S105

# Settings read from .env (see config/settings/_base.py).
SUPERUSER_SETTINGS = ("DJANGO_SUPERUSER_USERNAME", "DJANGO_SUPERUSER_EMAIL", "DJANGO_SUPERUSER_PASSWORD")

# Database hosts that count as local: this machine, the compose `db` service, and the Docker host. A blank host or a
# path (a Unix socket) counts too. Add yours if your local database lives somewhere else.
LOCAL_DB_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "db", "host.docker.internal"})


@dataclass(frozen=True)
class SeedLogin:
    email: str
    first_name: str
    last_name: str
    role: str = ""


ORGANIZATIONS = (
    ("dunder-mifflin", "Dunder Mifflin Paper Company, Inc."),
    ("pawnee-parks", "Pawnee Parks and Recreation"),
)

# Its email comes from .env, so `SUPERUSER` stands in for it in the tables below.
SUPERUSER = "superuser"
SUPERUSER_LOGIN = SeedLogin(SUPERUSER, "Leslie", "Knope", "Superuser and staff; owner of Pawnee Parks and Recreation")

LOGINS = (
    SeedLogin(
        "owner@example.com", "Michael", "Scott", "Owner of Dunder Mifflin; member of Pawnee Parks and Recreation"
    ),
    SeedLogin("member@example.com", "Dwight", "Schrute", "Member of Dunder Mifflin (not an owner)"),
    SeedLogin("user@example.com", "Ryan", "Howard", "No organization; pending invite to Dunder Mifflin"),
)


def _cast(domain: str, names: tuple[tuple[str, str], ...]) -> tuple[SeedLogin, ...]:
    return tuple(SeedLogin(f"{first}.{last}@{domain}".lower(), first, last) for first, last in names)


# Everyone else in each organization. Dunder Mifflin's 18 make a 20-member list, long enough to check layout and
# member search.
DUNDER_MIFFLIN_CAST = _cast(
    "dundermifflin.example",
    (
        ("Jim", "Halpert"),
        ("Pam", "Beesly"),
        ("Andy", "Bernard"),
        ("Angela", "Martin"),
        ("Kevin", "Malone"),
        ("Oscar", "Martinez"),
        ("Stanley", "Hudson"),
        ("Phyllis", "Vance"),
        ("Creed", "Bratton"),
        ("Kelly", "Kapoor"),
        ("Toby", "Flenderson"),
        ("Meredith", "Palmer"),
        ("Darryl", "Philbin"),
        ("Erin", "Hannon"),
        ("Gabe", "Lewis"),
        ("Nellie", "Bertram"),
        ("Pete", "Miller"),
        ("Clark", "Green"),
    ),
)
PAWNEE_CAST = _cast(
    "pawnee.example",
    (
        ("Ron", "Swanson"),
        ("Tom", "Haverford"),
        ("April", "Ludgate"),
        ("Andy", "Dwyer"),
        ("Ann", "Perkins"),
        ("Ben", "Wyatt"),
        ("Chris", "Traeger"),
        ("Donna", "Meagle"),
        ("Jerry", "Gergich"),
    ),
)
FILLERS = (*DUNDER_MIFFLIN_CAST, *PAWNEE_CAST)

# (organization slug, user email, is_owner, is_primary)
MEMBERSHIPS = (
    ("pawnee-parks", SUPERUSER, True, True),
    ("dunder-mifflin", "owner@example.com", True, True),
    ("pawnee-parks", "owner@example.com", False, False),
    ("dunder-mifflin", "member@example.com", False, True),
    *(("dunder-mifflin", member.email, False, True) for member in DUNDER_MIFFLIN_CAST),
    *(("pawnee-parks", member.email, False, True) for member in PAWNEE_CAST),
)

# (organization slug, team name, member emails)
TEAMS = (
    (
        "dunder-mifflin",
        "Sales",
        (
            "member@example.com",
            "jim.halpert@dundermifflin.example",
            "andy.bernard@dundermifflin.example",
            "stanley.hudson@dundermifflin.example",
            "phyllis.vance@dundermifflin.example",
        ),
    ),
    (
        "dunder-mifflin",
        "Party Planning Committee",
        (
            "angela.martin@dundermifflin.example",
            "pam.beesly@dundermifflin.example",
            "phyllis.vance@dundermifflin.example",
            "meredith.palmer@dundermifflin.example",
        ),
    ),
    (
        "pawnee-parks",
        "Harvest Festival",
        (
            SUPERUSER,
            "ron.swanson@pawnee.example",
            "tom.haverford@pawnee.example",
            "april.ludgate@pawnee.example",
            "ben.wyatt@pawnee.example",
        ),
    ),
)

# (organization slug, sender email, invitee email, is_expired). An invitee with a seeded login is linked to it.
INVITES = (
    ("dunder-mifflin", "owner@example.com", "user@example.com", False),
    ("dunder-mifflin", "owner@example.com", "holly.flax@dundermifflin.example", False),
    ("dunder-mifflin", "owner@example.com", "todd.packer@dundermifflin.example", True),
)


class Command(BaseCommand):
    help = "Create known dev logins, organizations, teams and invites (DEBUG only, idempotent)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(f"seed only runs with DEBUG on: every seeded login uses the password {SEED_PASSWORD!r}.")
        # Checked before the first query, so a remote database is never touched.
        host = connections[DEFAULT_DB_ALIAS].settings_dict.get("HOST") or ""
        if host and not host.startswith("/") and host not in LOCAL_DB_HOSTS:
            raise CommandError(
                f"seed only runs against a local database, not {host!r}: it creates a superuser and logins with a "
                "well-known password. If that host is local, add it to LOCAL_DB_HOSTS in "
                "apps/base/management/commands/seed.py."
            )
        credentials = tuple(getattr(settings, name, "") for name in SUPERUSER_SETTINGS)
        if not all(credentials):
            raise CommandError(
                f"Set {', '.join(SUPERUSER_SETTINGS)} in .env; seed makes that account the superuser. A new project's "
                "`just create_env` fills them in (see .env.toml)."
            )
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise CommandError("Migrations are still pending; retry once /api/app-context/ answers.")

        with transaction.atomic():
            users = self._seed_users(*credentials)
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
        rows = [(login.email, f"{login.first_name} {login.last_name}", login.role) for login in LOGINS]
        superuser = users[SUPERUSER]
        superuser_row = (superuser.email, superuser.get_full_name(), SUPERUSER_LOGIN.role)
        widths = [max(len(row[i]) for row in (*rows, superuser_row)) for i in range(2)]

        def write_row(email, name, role):
            self.stdout.write(f"    {email.ljust(widths[0])}  {name.ljust(widths[1])}  {role}")

        self.stdout.write(f'Sign in at {settings.SITE_URL}/accounts/login/ with the password "{SEED_PASSWORD}":')
        self.stdout.write("")
        for row in rows:
            write_row(*row)
        self.stdout.write("")
        self.stdout.write(
            f"Everyone else at Dunder Mifflin and Pawnee (e.g. {DUNDER_MIFFLIN_CAST[0].email}) uses the same password."
        )
        self.stdout.write("")
        # Never print the superuser's password: it may come from 1Password.
        self.stdout.write("The superuser signs in with DJANGO_SUPERUSER_PASSWORD from .env:")
        self.stdout.write("")
        write_row(*superuser_row)
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

    def _seed_users(self, superuser_username: str, superuser_email: str, superuser_password: str) -> dict[str, User]:
        # Hash once: the default hasher is deliberately slow, and every seeded user but the superuser shares it.
        password = make_password(SEED_PASSWORD)
        users = {}
        for login in (*LOGINS, *FILLERS):
            users[login.email] = self._seed_user(login.email, login, password=password, is_superuser=False)

        # Matching on the username alone would create a second account with the same email.
        taken = (
            User.objects.filter(Q(email__iexact=superuser_email) | Q(emailaddress__email__iexact=superuser_email))
            .exclude(username=superuser_username)
            .first()
        )
        if taken:
            raise CommandError(
                f"DJANGO_SUPERUSER_EMAIL ({superuser_email}) already belongs to the user {taken.username!r}. "
                "Use another email in .env, or delete that user."
            )
        users[SUPERUSER] = self._seed_user(
            superuser_email,
            SUPERUSER_LOGIN,
            username=superuser_username,
            password=make_password(superuser_password),
            is_superuser=True,
        )

        # Enrolling TOTP or a passkey turns on MFA, which would stop a known password from being enough.
        removed, _ = Authenticator.objects.filter(user__in=users.values()).delete()
        if removed:
            self.stdout.write(f"Removed {removed} MFA authenticator(s) from seeded logins.")
        return users

    @staticmethod
    def _seed_user(email: str, login: SeedLogin, *, password: str, is_superuser: bool, username: str = "") -> User:
        user, _ = User.objects.update_or_create(
            username=username or email,
            defaults={
                "email": email,
                "first_name": login.first_name,
                "last_name": login.last_name,
                "is_active": True,
                "is_staff": is_superuser,
                "is_superuser": is_superuser,
                "password": password,
            },
        )
        has_primary = EmailAddress.objects.filter(user=user, primary=True).exclude(email=email).exists()
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True},
            create_defaults={"verified": True, "primary": not has_primary},
        )
        return user

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
