from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class TestIndexView(TestCase):
    def test_index(self):
        res = self.client.get(reverse("site_index"))
        assert res.status_code == 200
        password = "test"
        user = User.objects.create_user(username="testuser", password=password)
        self.client.force_login(user)
        self.client.login(username=user.username, password=password)
        res = self.client.get(reverse("site_index"))
        assert res.status_code == 200
