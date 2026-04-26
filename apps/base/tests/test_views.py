from apps.base.tests import BaseTest


class TestIndexView(BaseTest):
    def test_index(self):
        # test not logged in
        self.get("site_index")
        self.assert_http_302_found()

        # test logged in — redirects to budget dashboard
        user = self.make_user()
        with self.login(user):
            self.get("site_index")
            self.assert_http_302_found()
