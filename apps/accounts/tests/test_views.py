# test account_email
from django.core import mail
from django.forms import model_to_dict

from allauth.account.models import EmailAddress

from apps.accounts.models import User
from apps.base.tests import BaseTest


class BaseAccountViewTest(BaseTest):
    def _test_not_logged_in(self) -> None:
        self.get(self.url_name)
        self.assert_http_302_found()


class TestChangeNameView(BaseAccountViewTest):
    url_name = "account_change_name"

    def test_view(self):
        self._test_not_logged_in()
        user = self.make_user()
        with self.login(user):
            self.get(self.url_name)
            self.assert_http_200_ok()

            # test making the change
            assert user.first_name == ""
            assert user.last_name == ""

            data = {
                "first_name": "New First",
                "last_name": "New Last",
            }
            self.post(self.url_name, data=data)
            self.assert_http_302_found()

            user = User.objects.get(pk=user.id)
            assert user.first_name == data["first_name"]
            assert user.last_name == data["last_name"]


class TestChangePasswordView(BaseAccountViewTest):
    url_name = "account_change_password"

    def test_view(self):
        self._test_not_logged_in()
        user = self.make_user()
        old_password_hash = user.password
        with self.login(user):
            self.get(self.url_name)
            self.assert_http_200_ok()

            data = {
                "oldpassword": "password",
                "password1": "new-password",
                "password2": "new-password",
            }
            self.post(self.url_name, data=data)
            self.assert_http_302_found()

            user = User.objects.get(pk=user.id)
            assert user.password != old_password_hash

        # attempt logging in with new password
        with self.login(user, password="new-password"):  # noqa: S106
            self.get("site_index")
            self.assert_http_200_ok()


class TestChangeEmailView(BaseAccountViewTest):
    url_name = "account_email"

    def test_view(self):
        self._test_not_logged_in()
        user = self.make_user()
        with self.login(user):
            test_email = "foo@example.com"

            # test get
            self.get(self.url_name)
            self.assert_http_200_ok()

            assert EmailAddress.objects.count() == 1

            # test add
            data = {
                "email": test_email,
                "action_add": "",
            }
            self.post(self.url_name, data=data)
            self.assert_http_302_found()

            assert EmailAddress.objects.count() == 2
            email_address = EmailAddress.objects.get(email=test_email)
            assert model_to_dict(email_address) == {
                "id": email_address.pk,
                "user": user.pk,
                "email": data["email"],
                "primary": False,
                "verified": False,
            }

            # test re-send verification
            data = {
                "email": test_email,
                "action_send": "",
            }
            self.post(self.url_name, data=data)
            self.assert_http_302_found()
            assert len(mail.outbox) == 2
            activate_url = self.get_context("activate_url")
            assert activate_url in mail.outbox[1].body

            # test verify
            self.get(activate_url)
            self.assert_http_302_found()
            email_address = EmailAddress.objects.get(email=test_email)
            assert email_address.verified is True

            # test make primary
            data = {
                "email": test_email,
                "action_primary": "",
            }
            self.post(self.url_name, data=data)
            self.assert_http_302_found()
            email_address = EmailAddress.objects.get(email=test_email)
            assert email_address.primary is True

            # test remove
            email_address.primary = False
            email_address.save()

            # first set the other email to the primary
            email_address_1 = EmailAddress.objects.get(email="testuser@example.com")
            email_address_1.primary = True
            email_address_1.save()

            data = {
                "email": test_email,
                "action_remove": "",
            }
            self.post(self.url_name, data=data)
            self.assert_http_302_found()
            assert EmailAddress.objects.count() == 1
            email_address = EmailAddress.objects.get(email="testuser@example.com")
            assert email_address.primary is True
