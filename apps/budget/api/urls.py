from django.urls import path

from . import views

urlpatterns = [
    path("", views.BudgetDetailAPIView.as_view(), name="budget-detail"),
    path("dashboard/", views.DashboardAPIView.as_view(), name="dashboard"),

    path("categories/", views.CategoryListAPIView.as_view(), name="category-list"),
    path("categories/<int:pk>/", views.CategoryDetailAPIView.as_view(), name="category-detail"),

    path("transactions/", views.TransactionListAPIView.as_view(), name="transaction-list"),
    path("transactions/<int:pk>/", views.TransactionDetailAPIView.as_view(), name="transaction-detail"),
    path("transactions/<int:pk>/mark-paid/", views.TransactionMarkPaidAPIView.as_view(), name="transaction-mark-paid"),

    path("recurring/", views.RecurringListAPIView.as_view(), name="recurring-list"),
    path("recurring/<int:pk>/", views.RecurringDetailAPIView.as_view(), name="recurring-detail"),

    path("overview/", views.BudgetOverviewAPIView.as_view(), name="budget-overview"),
    path("category-budgets/<int:category_pk>/", views.CategoryBudgetAPIView.as_view(), name="category-budget"),

    path("members/", views.MemberListAPIView.as_view(), name="member-list"),
    path("members/<int:pk>/", views.MemberDetailAPIView.as_view(), name="member-detail"),
]
