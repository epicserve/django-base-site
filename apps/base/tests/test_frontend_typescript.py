"""The SPA is TypeScript, so `vue-tsc` in `just lint` checks all of it against the generated API types."""

import json
import re

from django.conf import settings

FRONTEND = settings.BASE_DIR / "frontend"
FRONTEND_JS = FRONTEND / "js"
SCRIPT_TAG = re.compile(r"<script\b[^>]*>")


class TestFrontendIsTypeScript:
    def test_no_javascript_modules(self):
        # tsconfig.json doesn't allow JavaScript, so a `.js` module would be left out of the type check.
        assert sorted(str(path.relative_to(FRONTEND_JS)) for path in FRONTEND_JS.rglob("*.js")) == []

    def test_every_vue_script_is_typescript(self):
        # vue-tsc only type-checks a component whose <script> is `lang="ts"`.
        untyped = [
            f"{path.relative_to(FRONTEND_JS)}: {tag}"
            for path in sorted(FRONTEND_JS.rglob("*.vue"))
            for tag in SCRIPT_TAG.findall(path.read_text())
            if 'lang="ts"' not in tag
        ]
        assert untyped == []

    def test_tsconfig_does_not_allow_javascript(self):
        compiler_options = json.loads((FRONTEND / "tsconfig.json").read_text())["compilerOptions"]
        assert not compiler_options.get("allowJs", False)
        assert not compiler_options.get("checkJs", False)
