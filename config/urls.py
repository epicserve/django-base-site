from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from apps.accounts.views import NameChange, SignInView
from apps.base.views import http_404, http_500
from apps.budget.views import BudgetHistoryView, BudgetHomeView, PaymentMethodsView

# Includes
urlpatterns: list[URLResolver | URLPattern] = [path(r"admin/", admin.site.urls)]

# Project Urls
urlpatterns += [
    path("", BudgetHomeView.as_view(), name="site_index"),
    path("-/", include("django_alive.urls")),
    path("500/", http_500),
    path("404/", http_404),
    path("accounts/history/", BudgetHistoryView.as_view(), name="budget_history"),
    path("accounts/payment-methods/", PaymentMethodsView.as_view(), name="payment_methods"),
    path("accounts/name/", NameChange.as_view(), name="account_change_name"),
    path("accounts/login/", SignInView.as_view(), name="account_login"),
    path("accounts/", include("allauth.urls")),
    path("budgets/", include("apps.budget.urls", namespace="budget")),
    path("api/budgets/<int:budget_pk>/", include("apps.budget.api.urls")),
    path("api/payment-methods/", include("apps.budget.api.payment_methods_urls")),
]

# Debug/Development URLs
if settings.DEBUG is True:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("admin/doc/", include("django.contrib.admindocs.urls")),
    ]
