"""The GitHub Actions workflows must install `just` in a way that doesn't fail on GitHub's API rate limit."""

from django.conf import settings

WORKFLOWS = sorted((settings.BASE_DIR / ".github" / "workflows").glob("*.yml"))


class TestCIWorkflows:
    def test_workflows_found(self):
        assert WORKFLOWS

    def test_just_is_not_installed_with_the_install_script(self):
        # just.systems/install.sh looks up the latest release with an unauthenticated GitHub API call, which runners
        # share per IP, so jobs failed at random with a 403. extractions/setup-just authenticates with the job's token.
        for workflow in WORKFLOWS:
            assert "just.systems/install.sh" not in workflow.read_text(), workflow.name

    def test_workflows_that_run_just_install_it_with_setup_just(self):
        for workflow in WORKFLOWS:
            text = workflow.read_text()
            if "just " in text:
                assert "uses: extractions/setup-just@" in text, workflow.name
