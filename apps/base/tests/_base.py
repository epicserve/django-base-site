from django.test import Client, TestCase

from apps.accounts.models import User
from apps.base.tests import sign_in as sign_in_module
from apps.organizations.models import Organization


class BaseTest(TestCase):
    def sign_in(self, user: User, org: Organization | None = None) -> Client:
        """Sign `self.client` in as `user` with `org` selected; see `apps.base.tests.sign_in.sign_in`."""
        return sign_in_module.sign_in(self.client, user, org)
