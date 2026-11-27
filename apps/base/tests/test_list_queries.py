"""Every list endpoint takes the same number of queries however many rows it lists, so none runs a query per row."""

from apps.accounts.recipes import make_superuser, make_user
from apps.base.tests import BaseTest
from apps.notifications.recipes import make_notification
from apps.organizations.recipes import make_invite, make_member, make_org
from apps.teams.recipes import make_team
from config.api import api

# GET routes that return a list built from settings, not from database rows, so they can't run a query per row.
NOT_FROM_THE_DATABASE = {
    "/api/notifications/preferences/": "a row per NOTIFICATIONS_CATEGORIES entry, with the saved ones in one query",
    "/api/billing/plans/": "BILLING_PLANS",
    "/api/billing/features/": "BILLING_FEATURES",
}


class TestListQueries(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user(first_name="Michael", last_name="Scott")
        cls.org = make_org(cls.owner)
        cls.superuser = make_superuser()
        # One row in every list to start with, so a prefetch that skips an empty list isn't mistaken for growth.
        cls.member = make_member(cls.org)
        make_invite(cls.org, cls.owner, invitee=make_user())
        make_team(cls.org, members=[cls.owner, cls.member])
        make_notification(cls.owner, organization=cls.org, actor=cls.member)

    def add_members(self, count=3):
        return [make_member(self.org) for _ in range(count)]

    def test_users(self):
        self.sign_in(self.owner, self.org)
        self.assert_queries_dont_grow("/api/users/", self.add_members)

    def test_impersonate_search(self):
        self.sign_in(self.superuser)
        self.assert_queries_dont_grow("/api/users/impersonate-search/", lambda: [make_user() for _ in range(3)])

    def test_staff_users(self):
        self.sign_in(self.superuser)
        self.assert_queries_dont_grow(
            "/api/test-notifications/staff-users/", lambda: [make_user(is_staff=True) for _ in range(3)]
        )

    def test_switch_list(self):
        self.sign_in(self.owner, self.org)
        self.assert_queries_dont_grow(
            "/api/organizations/switch-list/", lambda: [make_org(self.owner) for _ in range(3)]
        )

    def test_members(self):
        self.sign_in(self.owner, self.org)
        self.assert_queries_dont_grow("/api/organization-members/", self.add_members)

    def test_invites(self):
        self.sign_in(self.owner, self.org)
        self.assert_queries_dont_grow(
            "/api/organization-invites/",
            lambda: [make_invite(self.org, self.owner, invitee=make_user()) for _ in range(3)],
        )

    def test_teams(self):
        self.sign_in(self.owner, self.org)
        self.assert_queries_dont_grow(
            "/api/teams/", lambda: [make_team(self.org, members=[self.owner, *self.add_members(2)]) for _ in range(3)]
        )

    def test_notifications(self):
        self.sign_in(self.owner, self.org)
        self.assert_queries_dont_grow(
            "/api/notifications/",
            lambda: [
                make_notification(self.owner, organization=self.org, actor=member) for member in self.add_members()
            ],
        )


# Each list route and the TestListQueries test that checks it.
LISTS_TESTED = {
    "/api/users/": "test_users",
    "/api/users/impersonate-search/": "test_impersonate_search",
    "/api/test-notifications/staff-users/": "test_staff_users",
    "/api/organizations/switch-list/": "test_switch_list",
    "/api/organization-members/": "test_members",
    "/api/organization-invites/": "test_invites",
    "/api/teams/": "test_teams",
    "/api/notifications/": "test_notifications",
}


def list_routes():
    """GET routes whose 200 body is an array, or a page of one (`results`)."""
    schema = api.get_openapi_schema()
    components = schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        content = operations.get("get", {}).get("responses", {}).get(200, {}).get("content", {})
        body = content.get("application/json", {}).get("schema", {})
        if "$ref" in body:
            body = components[body["$ref"].rsplit("/", 1)[-1]].get("properties", {}).get("results", {})
        if body.get("type") == "array":
            yield path


class TestEveryListIsChecked:
    def test_every_list_route_has_a_query_count_test(self):
        # Billing's routes are mounted only with BILLING_ENABLED, so they may be missing here.
        assert len(set(list_routes())) > 5, "Found fewer list routes than expected; has the OpenAPI schema changed?"
        unchecked = sorted(set(list_routes()) - set(LISTS_TESTED) - set(NOT_FROM_THE_DATABASE))
        assert unchecked == [], "Add a test to TestListQueries for each, and list it in LISTS_TESTED"

    def test_each_named_test_exists(self):
        assert [name for name in LISTS_TESTED.values() if not hasattr(TestListQueries, name)] == []
        assert set(LISTS_TESTED) <= set(list_routes()), "LISTS_TESTED names a route that's gone or isn't a list"
