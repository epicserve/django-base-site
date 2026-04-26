from django.urls import path

from apps.budget import views

app_name = "budget"

urlpatterns = [
    # Budget
    path("", views.BudgetListView.as_view(), name="list"),
    path("create/", views.BudgetCreateView.as_view(), name="create"),
    path("<int:budget_pk>/", views.BudgetDetailView.as_view(), name="detail"),
    path("<int:budget_pk>/delete/", views.BudgetDeleteView.as_view(), name="delete"),
    # Members
    path("<int:budget_pk>/members/", views.MemberListView.as_view(), name="member-list"),
    path("<int:budget_pk>/members/invite/", views.MemberInviteView.as_view(), name="member-invite"),
    path("<int:budget_pk>/members/<int:pk>/remove/", views.MemberRemoveView.as_view(), name="member-remove"),
    # Categories
    path("<int:budget_pk>/categories/", views.CategoryListView.as_view(), name="category-list"),
    path("<int:budget_pk>/categories/create/", views.CategoryCreateView.as_view(), name="category-create"),
    path("<int:budget_pk>/categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category-edit"),
    path("<int:budget_pk>/categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category-delete"),
    # Transactions
    path("<int:budget_pk>/transactions/", views.TransactionListView.as_view(), name="transaction-list"),
    path("<int:budget_pk>/transactions/create/", views.TransactionCreateView.as_view(), name="transaction-create"),
    path("<int:budget_pk>/transactions/<int:pk>/", views.TransactionDetailView.as_view(), name="transaction-detail"),
    path("<int:budget_pk>/transactions/<int:pk>/edit/", views.TransactionUpdateView.as_view(), name="transaction-edit"),
    path("<int:budget_pk>/transactions/<int:pk>/delete/", views.TransactionDeleteView.as_view(), name="transaction-delete"),
    path("<int:budget_pk>/transactions/<int:pk>/mark-paid/", views.TransactionMarkPaidView.as_view(), name="transaction-mark-paid"),
    # Recurring
    path("<int:budget_pk>/recurring/", views.RecurringListView.as_view(), name="recurring-list"),
    path("<int:budget_pk>/recurring/create/", views.RecurringCreateView.as_view(), name="recurring-create"),
    path("<int:budget_pk>/recurring/<int:pk>/", views.RecurringDetailView.as_view(), name="recurring-detail"),
    path("<int:budget_pk>/recurring/<int:pk>/edit/", views.RecurringUpdateView.as_view(), name="recurring-edit"),
    path("<int:budget_pk>/recurring/<int:pk>/delete/", views.RecurringDeleteView.as_view(), name="recurring-delete"),
]
