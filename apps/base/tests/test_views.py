SPA_SHELL = "layouts/spa_shell.html"


class TestSPAShell:
    def test_root_returns_spa_shell(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert SPA_SHELL in [template.name for template in resp.templates]

    def test_unknown_path_returns_spa_shell(self, client):
        resp = client.get("/some/random/path/")
        assert resp.status_code == 200
        assert SPA_SHELL in [template.name for template in resp.templates]

    def test_public_static_404_does_not_return_spa_shell(self, client):
        resp = client.get("/public/static/dist/js/missing-chunk.js")
        assert resp.status_code == 404
