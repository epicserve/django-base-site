"""
Sign a test client in without going through the sign-in form or API.

Only tests of signing in itself should sign in through allauth (`api_sign_in`) or the form (in e2e tests). Everything
else uses `sign_in`, which is faster and doesn't depend on the sign-in flow working.
"""

from django.http import HttpRequest
from django.test import Client

from allauth.account.internal.flows.login import record_authentication

from apps.accounts.models import User
from apps.accounts.recipes import TEST_PASSWORD
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.session import remove_org, save_org_data


def sign_in(client: Client, user: User, org: Organization | None = None) -> Client:
    """
    Sign `client` in as `user` with `org` selected, as signing in with a password would leave the session.

    `org` defaults to the user's primary organization, which is what signing in selects. Django's `force_login` doesn't
    select one: the login signal's receiver needs `request.user`, and `force_login`'s request has none. The session also
    records a password sign-in, so allauth doesn't ask the user to sign in again before a change that needs a recent
    one, such as setting up two-factor authentication or adding a passkey.
    """
    client.force_login(user)
    request = HttpRequest()
    request.user = user
    request.session = client.session
    if org is None:
        membership = OrganizationMember.objects.filter(user=user, is_primary=True).select_related("organization")
        org = next((member.organization for member in membership), None)
    if org is None:
        remove_org(request)
    else:
        save_org_data(request, org)
    record_authentication(request, user, method="password", email=user.email)
    request.session.save()
    return client


def api_sign_in(client: Client, email: str, password: str = TEST_PASSWORD):
    """Sign in through allauth's headless API, for tests of signing in itself. Returns the response."""
    return client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": email, "password": password},
        content_type="application/json",
    )
