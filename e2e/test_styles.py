"""End-to-end check that the built SPA loads its stylesheet, which the Vite dev server would inject from the script."""

from playwright.sync_api import Page, expect


class TestStylesheet:
    def test_the_built_spa_applies_its_tailwind_styles(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/login/")

        # spa_shell.html gives <body> `bg-white`; without the stylesheet it's transparent.
        expect(page.locator("body")).to_have_css("background-color", "rgb(255, 255, 255)")
