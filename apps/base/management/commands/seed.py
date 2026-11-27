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
the password alone. Apart from that it never deletes anything created by hand:

- Team members are only added, never removed.
- `is_primary` (on memberships and email addresses) is only set when a row is
  created and the user has no primary yet, because users change it in the app.
- An invite whose invitee has since joined the organization is skipped, since
  accepting an invite deletes it and creates the membership.

Every row is built with the same recipes the tests use (`apps/<app>/recipes.py`),
called with `update=True`, so seeded data and test data can't drift apart.
"""

from dataclasses import dataclass

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import Q

from allauth.mfa.models import Authenticator

from apps.accounts.models import User
from apps.accounts.recipes import make_user
from apps.organizations.models import Organization, OrganizationInvite
from apps.organizations.recipes import make_invite, make_member, make_org
from apps.organizations.roles import OrgRole
from apps.teams.recipes import make_team

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


# Everyone else in each organization. Dunder Mifflin's 18 make a 20-member list, long enough to check layout.
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

# (organization slug, user email, role, is_primary)
MEMBERSHIPS = (
    ("pawnee-parks", SUPERUSER, OrgRole.OWNER, True),
    ("dunder-mifflin", "owner@example.com", OrgRole.OWNER, True),
    ("pawnee-parks", "owner@example.com", OrgRole.MEMBER, False),
    ("dunder-mifflin", "member@example.com", OrgRole.MEMBER, True),
    *(("dunder-mifflin", member.email, OrgRole.MEMBER, True) for member in DUNDER_MIFFLIN_CAST),
    *(("pawnee-parks", member.email, OrgRole.MEMBER, True) for member in PAWNEE_CAST),
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

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Change nothing; fail unless the seeded logins and organizations exist (`just doctor` runs this).",
        )

    def handle(self, *args, **options):
        if options["check"]:
            self._check()
            return
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

    def _check(self) -> None:
        """Fail, naming what's missing, unless the logins and organizations `seed` makes exist. Reads only."""
        emails = [login.email for login in LOGINS]
        found = {email.lower() for email in User.objects.filter(email__in=emails).values_list("email", flat=True)}
        missing = [email for email in emails if email.lower() not in found]
        superuser_username = getattr(settings, "DJANGO_SUPERUSER_USERNAME", "")
        if superuser_username and not User.objects.filter(username=superuser_username, is_superuser=True).exists():
            missing.append(f"the superuser {superuser_username!r}")
        slugs = {slug for slug, _ in ORGANIZATIONS}
        missing += sorted(slugs - set(Organization.objects.filter(slug__in=slugs).values_list("slug", flat=True)))
        if missing:
            raise CommandError(f"Not seeded: {', '.join(missing)} missing. Run just seed.")
        self.stdout.write("The seeded logins and organizations exist.")

    def _seed_users(self, superuser_username: str, superuser_email: str, superuser_password: str) -> dict[str, User]:
        users = {}
        for login in (*LOGINS, *FILLERS):
            users[login.email] = self._seed_user(login.email, login, password=SEED_PASSWORD, is_superuser=False)

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
            password=superuser_password,
            is_superuser=True,
        )

        # Enrolling TOTP or a passkey turns on MFA, which would stop a known password from being enough.
        removed, _ = Authenticator.objects.filter(user__in=users.values()).delete()
        if removed:
            self.stdout.write(f"Removed {removed} MFA authenticator(s) from seeded logins.")
        return users

    @staticmethod
    def _seed_user(email: str, login: SeedLogin, *, password: str, is_superuser: bool, username: str = "") -> User:
        return make_user(
            email,
            username=username or email,
            password=password,
            first_name=login.first_name,
            last_name=login.last_name,
            is_active=True,
            is_staff=is_superuser,
            is_superuser=is_superuser,
            update=True,
        )

    def _seed_organizations(self) -> dict[str, Organization]:
        return {slug: make_org(name=name, slug=slug, update=True) for slug, name in ORGANIZATIONS}

    def _seed_memberships(self, users: dict[str, User], orgs: dict[str, Organization]) -> None:
        for slug, email, role, is_primary in MEMBERSHIPS:
            # True means "if they have no primary membership yet", which is make_member's own rule.
            make_member(orgs[slug], users[email], role=role, is_primary=None if is_primary else False, update=True)

    def _seed_teams(self, users: dict[str, User], orgs: dict[str, Organization]) -> None:
        for slug, name, emails in TEAMS:
            make_team(orgs[slug], name, [users[email] for email in emails], update=True)

    def _seed_invites(self, users: dict[str, User], orgs: dict[str, Organization]) -> list[OrganizationInvite]:
        invites = []
        for slug, sender_email, email, is_expired in INVITES:
            org = orgs[slug]
            if org.organizationmember_set.filter(user__email__iexact=email).exists():
                self.stdout.write(f"{email} is already a member of {org}, skipping their invite.")
                continue
            invites.append(
                make_invite(
                    org, users[sender_email], email=email, invitee=users.get(email), expired=is_expired, update=True
                )
            )
        return invites
