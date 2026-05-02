from django.test import TestCase


class TestSPAShell(TestCase):
    def test_root_returns_spa_shell(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "layouts/spa_shell.html")

    def test_unknown_path_returns_spa_shell(self):
        resp = self.client.get("/some/random/path/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "layouts/spa_shell.html")

    def test_public_static_404_does_not_return_spa_shell(self):
        resp = self.client.get("/public/static/dist/js/missing-chunk.js")
        self.assertEqual(resp.status_code, 404)
