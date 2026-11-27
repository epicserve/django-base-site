import re
from collections import Counter
from collections.abc import Callable

from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import User
from apps.base.tests import sign_in as sign_in_module
from apps.organizations.models import Organization


class BaseTest(TestCase):
    def sign_in(self, user: User, org: Organization | None = None) -> Client:
        """Sign `self.client` in as `user` with `org` selected; see `apps.base.tests.sign_in.sign_in`."""
        return sign_in_module.sign_in(self.client, user, org)

    def assert_queries_dont_grow(self, url: str, add_rows: Callable[[], object], *, min_new_rows: int = 3) -> None:
        """
        Fail when the list at `url` runs more queries for more rows: a query per row (N+1).

        GETs `url` once to warm up (the first request can load the session or fill a cache), then once with the rows
        the class already has, then calls `add_rows` and GETs it again. The second list must show at least
        `min_new_rows` more rows than the first, and both must take the same number of queries. Start from at least
        one row, so a `prefetch_related` that skips an empty list doesn't count as growth, and keep the total under
        the endpoint's page size. The rows `add_rows` makes should use every relation the endpoint shows (an invite's
        invitee, a notification's actor, a team's members), or a missing `select_related` won't show.
        """
        self._list_and_queries(url)
        rows_before, before = self._list_and_queries(url)
        add_rows()
        rows_after, after = self._list_and_queries(url)
        assert rows_after >= rows_before + min_new_rows, (
            f"{url} listed {rows_before} rows, then {rows_after}: add_rows() should add rows it lists"
        )
        extra = Counter(map(_without_values, after)) - Counter(map(_without_values, before))
        assert len(after) == len(before), (
            f"{url} ran {len(before)} queries for {rows_before} rows and {len(after)} for {rows_after}. "
            "Queries that repeat per row:\n" + "\n".join(f"{count} more of: {sql}" for sql, count in extra.items())
        )

    def _list_and_queries(self, url: str) -> tuple[int, list[str]]:
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        assert response.status_code == 200, response.content
        body = response.json()
        rows = body["results"] if isinstance(body, dict) else body
        return len(rows), [query["sql"] for query in queries.captured_queries]


def _without_values(sql: str) -> str:
    """Replace the quoted values and numbers in `sql` with `?`, so the same query for another row compares equal."""
    return re.sub(r"'[^']*'|\b\d+\b", "?", sql)
