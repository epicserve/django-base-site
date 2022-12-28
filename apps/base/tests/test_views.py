from apps.base.tests import BaseTest


class TestIndexView(BaseTest):
    def test_index(self):
        # test not logged in
        self.get("site_index")
        self.assert_http_200_ok()

        # test logged in
        user = self.make_user()
        with self.login(user):
            self.get("site_index")
            self.assert_http_200_ok()
