"""Single ``NinjaAPI`` instance for the project, mounted at ``/api/`` in config/urls.py."""

from django.conf import settings

from ninja import NinjaAPI
from ninja.security import django_auth

from apps.accounts.api import avatar_router, users_router
from apps.base.api import router as base_router
from apps.base.errors import register_error_handlers
from apps.organizations.api import (
    invites_router as org_invites_router,
)
from apps.organizations.api import (
    members_router as org_members_router,
)
from apps.organizations.api import (
    orgs_router,
)
from apps.organizations.api import (
    settings_router as org_settings_router,
)
from apps.teams.api import router as teams_router

api = NinjaAPI(
    title="Django Base Site API",
    version="1.0.0",
    auth=django_auth,  # django_auth is a SessionAuth — CSRF enforcement is built in.
    docs_url="/docs" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

register_error_handlers(api)

api.add_router("/", base_router)
api.add_router("/avatar/", avatar_router)
api.add_router("/organization-invites/", org_invites_router)
api.add_router("/organization-members/", org_members_router)
api.add_router("/organization-settings/", org_settings_router)
api.add_router("/organizations/", orgs_router)
api.add_router("/teams/", teams_router)
api.add_router("/users/", users_router)
