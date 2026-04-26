import calendar
import datetime

from django.conf import settings as django_settings

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views import generic

from apps.budget.forms import (
    CategoryForm,
    MemberInviteForm,
    RecurringTransactionForm,
    TransactionForm,
    make_transaction_line_formset,
)
from apps.budget.models import Budget, BudgetMembership, Category, PaymentMethod, RecurringTransaction, Transaction

from apps.accounts.models import User


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class BudgetMemberMixin(LoginRequiredMixin):
    """Verify the requesting user is a member of the budget identified by budget_pk."""

    budget: Budget

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        budget_pk = kwargs.get("budget_pk")
        try:
            self.budget = Budget.objects.get(pk=budget_pk)
        except Budget.DoesNotExist:
            raise Http404
        if not self.budget.members.filter(pk=request.user.pk).exists():
            raise Http404
        self.check_budget_permissions(request)
        return super().dispatch(request, *args, **kwargs)

    def check_budget_permissions(self, request):
        """Hook for subclasses to add extra permission checks after self.budget is set."""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["budget"] = self.budget
        return ctx


class BudgetOwnerMixin(BudgetMemberMixin):
    """Restrict to budget owners only."""

    def check_budget_permissions(self, request):
        is_owner = BudgetMembership.objects.filter(
            budget=self.budget, user=request.user, role=BudgetMembership.ROLE_OWNER
        ).exists()
        if not is_owner:
            raise Http404


# ---------------------------------------------------------------------------
# Budget CRUD
# ---------------------------------------------------------------------------


class PaymentMethodsView(LoginRequiredMixin, generic.TemplateView):
    template_name = "budget/payment_methods.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["payment_methods"] = PaymentMethod.objects.filter(user=self.request.user)
        ctx["type_choices"] = PaymentMethod.TYPE_CHOICES
        return ctx


class BudgetHistoryView(LoginRequiredMixin, generic.TemplateView):
    template_name = "budget/history.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        budget = Budget.objects.filter(members=self.request.user).first()
        ctx["budget"] = budget
        if budget:
            # Get all distinct year/month combinations that have transactions
            from django.db.models.functions import TruncMonth
            months = (
                Transaction.objects.filter(budget=budget)
                .annotate(month=TruncMonth("due_date"))
                .values("month")
                .distinct()
                .order_by("-month")
            )
            ctx["months"] = months
        return ctx


class BudgetHomeView(LoginRequiredMixin, View):
    """Redirect to the user's budget for the current month, creating one if needed."""

    def get(self, request):
        budget = Budget.objects.filter(members=request.user).first()
        if not budget:
            budget = Budget.objects.create(created_by=request.user)
            BudgetMembership.objects.create(budget=budget, user=request.user, role=BudgetMembership.ROLE_OWNER)
        return redirect(reverse("budget:detail", kwargs={"budget_pk": budget.pk}))


class BudgetListView(LoginRequiredMixin, generic.ListView):
    template_name = "budget/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        return Budget.objects.filter(members=self.request.user)


class BudgetCreateView(LoginRequiredMixin, View):
    def post(self, request):
        budget = Budget.objects.create(created_by=request.user)
        BudgetMembership.objects.create(budget=budget, user=request.user, role=BudgetMembership.ROLE_OWNER)
        return redirect(reverse("budget:detail", kwargs={"budget_pk": budget.pk}))

    def get(self, request):
        return redirect(reverse("budget:list"))


class BudgetDetailView(BudgetMemberMixin, generic.TemplateView):
    template_name = "budget/dashboard.html"


class BudgetDeleteView(BudgetOwnerMixin, generic.DeleteView):
    model = Budget
    template_name = "budget/budget_confirm_delete.html"
    pk_url_kwarg = "budget_pk"
    success_url = reverse_lazy("budget:list")


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class MemberListView(BudgetOwnerMixin, generic.ListView):
    template_name = "budget/member_list.html"
    context_object_name = "memberships"

    def get_queryset(self):
        return BudgetMembership.objects.filter(budget=self.budget).select_related("user")


class MemberInviteView(BudgetOwnerMixin, generic.FormView):
    form_class = MemberInviteForm
    template_name = "budget/member_invite_form.html"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        role = form.cleaned_data["role"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            form.add_error("email", f"No account found for {email}.")
            return self.form_invalid(form)
        _, created = BudgetMembership.objects.get_or_create(
            budget=self.budget,
            user=user,
            defaults={"role": role},
        )
        if not created:
            messages.warning(self.request, f"{email} is already a member of this budget.")
        else:
            messages.success(self.request, f"{email} has been added to the budget.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:member-list", kwargs={"budget_pk": self.budget.pk})


class MemberRemoveView(BudgetOwnerMixin, generic.DeleteView):
    model = BudgetMembership
    template_name = "budget/member_confirm_remove.html"
    context_object_name = "membership"

    def get_object(self, queryset=None):
        return get_object_or_404(BudgetMembership, pk=self.kwargs["pk"], budget=self.budget)

    def form_valid(self, form):
        membership = self.get_object()
        if membership.user == self.request.user:
            messages.error(self.request, "You cannot remove yourself from a budget.")
            return redirect(self.get_success_url())
        owner_count = BudgetMembership.objects.filter(budget=self.budget, role=BudgetMembership.ROLE_OWNER).count()
        if membership.role == BudgetMembership.ROLE_OWNER and owner_count <= 1:
            messages.error(self.request, "Cannot remove the last owner of a budget.")
            return redirect(self.get_success_url())
        membership.delete()
        messages.success(self.request, "Member removed.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:member-list", kwargs={"budget_pk": self.budget.pk})


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategoryListView(BudgetMemberMixin, generic.ListView):
    template_name = "budget/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(budget=self.budget)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["sections"] = [
            (Category.TYPE_INCOME, "Income", "success", qs.filter(category_type=Category.TYPE_INCOME)),
            (Category.TYPE_EXPENSE, "Expense", "danger", qs.filter(category_type=Category.TYPE_EXPENSE)),
        ]
        return ctx


class CategoryCreateView(BudgetMemberMixin, generic.CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "budget/category_form.html"

    def form_valid(self, form):
        form.instance.budget = self.budget
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors and try again.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:category-list", kwargs={"budget_pk": self.budget.pk})


class CategoryUpdateView(BudgetMemberMixin, generic.UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "budget/category_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Category, pk=self.kwargs["pk"], budget=self.budget)

    def get_success_url(self):
        return reverse("budget:category-list", kwargs={"budget_pk": self.budget.pk})


class CategoryDeleteView(BudgetMemberMixin, generic.DeleteView):
    model = Category
    template_name = "budget/category_confirm_delete.html"
    context_object_name = "category"

    def get_object(self, queryset=None):
        return get_object_or_404(Category, pk=self.kwargs["pk"], budget=self.budget)

    def form_valid(self, form):
        try:
            self.get_object().delete()
            messages.success(self.request, "Category deleted.")
        except ProtectedError:
            messages.error(self.request, "This category has transactions and cannot be deleted.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:category-list", kwargs={"budget_pk": self.budget.pk})


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class TransactionListView(BudgetMemberMixin, generic.ListView):
    template_name = "budget/transaction_list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        qs = Transaction.objects.filter(budget=self.budget).prefetch_related("lines__category")
        month_str = self.request.GET.get("month")
        if month_str:
            try:
                month_start = datetime.date.fromisoformat(month_str + "-01")
                last_day = calendar.monthrange(month_start.year, month_start.month)[1]
                month_end = month_start.replace(day=last_day)
                qs = qs.filter(due_date__range=(month_start, month_end))
            except (ValueError, TypeError):
                pass
        type_filter = self.request.GET.get("type")
        if type_filter in (Category.TYPE_INCOME, Category.TYPE_EXPENSE):
            qs = qs.filter(lines__category__category_type=type_filter).distinct()
        return qs


class TransactionCreateView(BudgetMemberMixin, generic.CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "budget/transaction_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        FormSet = make_transaction_line_formset(budget=self.budget)
        if self.request.POST:
            ctx["line_formset"] = FormSet(self.request.POST, prefix="lines")
        else:
            ctx["line_formset"] = FormSet(prefix="lines")
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        line_formset = ctx["line_formset"]
        if not line_formset.is_valid():
            errors = "; ".join(
                str(e) for e in line_formset.non_form_errors()
            ) or "Please check the line items."
            messages.error(self.request, errors)
            return redirect(self.get_success_url())
        form.instance.budget = self.budget
        form.instance.created_by = self.request.user
        with db_transaction.atomic():
            self.object = form.save()
            line_formset.instance = self.object
            line_formset.save()
        messages.success(self.request, "Transaction added.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors and try again.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:detail", kwargs={"budget_pk": self.budget.pk})


class TransactionDetailView(BudgetMemberMixin, generic.DetailView):
    model = Transaction
    template_name = "budget/transaction_detail.html"
    context_object_name = "transaction"

    def get_object(self, queryset=None):
        return get_object_or_404(Transaction, pk=self.kwargs["pk"], budget=self.budget)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lines"] = self.object.lines.select_related("category").all()
        return ctx


class TransactionUpdateView(BudgetMemberMixin, generic.UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "budget/transaction_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Transaction, pk=self.kwargs["pk"], budget=self.budget)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        FormSet = make_transaction_line_formset(budget=self.budget, extra=0)
        if self.request.POST:
            ctx["line_formset"] = FormSet(self.request.POST, instance=self.object, prefix="lines")
        else:
            ctx["line_formset"] = FormSet(instance=self.object, prefix="lines")
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        line_formset = ctx["line_formset"]
        if not line_formset.is_valid():
            return self.form_invalid(form)
        with db_transaction.atomic():
            self.object = form.save()
            line_formset.instance = self.object
            line_formset.save()
        messages.success(self.request, "Transaction updated.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:transaction-detail", kwargs={"budget_pk": self.budget.pk, "pk": self.object.pk})


class TransactionDeleteView(BudgetMemberMixin, generic.DeleteView):
    model = Transaction
    template_name = "budget/transaction_confirm_delete.html"
    context_object_name = "transaction"

    def get_object(self, queryset=None):
        return get_object_or_404(Transaction, pk=self.kwargs["pk"], budget=self.budget)

    def get_success_url(self):
        return reverse("budget:transaction-list", kwargs={"budget_pk": self.budget.pk})


class TransactionMarkPaidView(BudgetMemberMixin, View):
    def post(self, request, budget_pk, pk):
        transaction = get_object_or_404(Transaction, pk=pk, budget=self.budget)
        transaction.is_paid = not transaction.is_paid
        transaction.paid_date = datetime.date.today() if transaction.is_paid else None
        transaction.save(update_fields=["is_paid", "paid_date"])
        next_url = request.POST.get("next") or reverse("budget:transaction-detail", kwargs={"budget_pk": budget_pk, "pk": pk})
        return redirect(next_url)


# ---------------------------------------------------------------------------
# Recurring Transactions
# ---------------------------------------------------------------------------


class RecurringListView(BudgetMemberMixin, generic.ListView):
    template_name = "budget/recurring_list.html"
    context_object_name = "recurring_transactions"

    def get_queryset(self):
        return RecurringTransaction.objects.filter(budget=self.budget).select_related("category")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.filter(budget=self.budget).order_by("category_type", "name")
        return ctx


class RecurringCreateView(BudgetMemberMixin, generic.CreateView):
    model = RecurringTransaction
    form_class = RecurringTransactionForm
    template_name = "budget/recurring_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["budget"] = self.budget
        return kwargs

    def form_valid(self, form):
        form.instance.budget = self.budget
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # Generate instances up to 3 months ahead
        lookahead = getattr(django_settings, "BUDGET_RECURRING_LOOKAHEAD_MONTHS", 3)
        today = datetime.date.today()
        year = today.year + (today.month + lookahead - 1) // 12
        month = (today.month + lookahead - 1) % 12 + 1
        through_date = today.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])
        self.object.generate_instances_up_to(through_date)
        messages.success(self.request, "Recurring transaction created and instances generated.")
        return response

    def get_success_url(self):
        return reverse("budget:recurring-detail", kwargs={"budget_pk": self.budget.pk, "pk": self.object.pk})


class RecurringDetailView(BudgetMemberMixin, generic.DetailView):
    model = RecurringTransaction
    template_name = "budget/recurring_detail.html"
    context_object_name = "recurring"

    def get_object(self, queryset=None):
        return get_object_or_404(RecurringTransaction, pk=self.kwargs["pk"], budget=self.budget)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["instances"] = (
            Transaction.objects.filter(recurring=self.object)
            .order_by("due_date")
        )
        ctx["categories"] = Category.objects.filter(budget=self.budget).order_by("category_type", "name")
        return ctx


class RecurringUpdateView(BudgetMemberMixin, generic.UpdateView):
    model = RecurringTransaction
    form_class = RecurringTransactionForm
    template_name = "budget/recurring_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(RecurringTransaction, pk=self.kwargs["pk"], budget=self.budget)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["budget"] = self.budget
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # If the user checked "delete future unpaid instances", remove them
        if self.request.POST.get("delete_future_unpaid"):
            today = datetime.date.today()
            Transaction.objects.filter(
                recurring=self.object,
                is_paid=False,
                due_date__gt=today,
            ).delete()
            # Reset generated_through so they get regenerated
            self.object.generated_through = None
            self.object.save(update_fields=["generated_through"])
            # Regenerate
            lookahead = getattr(django_settings, "BUDGET_RECURRING_LOOKAHEAD_MONTHS", 3)
            today = datetime.date.today()
            year = today.year + (today.month + lookahead - 1) // 12
            month = (today.month + lookahead - 1) % 12 + 1
            through_date = today.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])
            self.object.generate_instances_up_to(through_date)
            messages.success(self.request, "Schedule updated and future unpaid instances regenerated.")
        else:
            messages.success(self.request, "Schedule updated. Existing instances unchanged.")
        return response

    def get_success_url(self):
        return reverse("budget:recurring-detail", kwargs={"budget_pk": self.budget.pk, "pk": self.object.pk})


class RecurringDeleteView(BudgetMemberMixin, generic.DeleteView):
    model = RecurringTransaction
    template_name = "budget/recurring_confirm_delete.html"
    context_object_name = "recurring"

    def get_object(self, queryset=None):
        return get_object_or_404(RecurringTransaction, pk=self.kwargs["pk"], budget=self.budget)

    def form_valid(self, form):
        recurring = self.get_object()
        delete_future = self.request.POST.get("delete_future_unpaid")
        if delete_future:
            today = datetime.date.today()
            Transaction.objects.filter(recurring=recurring, is_paid=False, due_date__gt=today).delete()
        # Soft-delete: deactivate rather than hard-delete
        recurring.is_active = False
        recurring.end_date = datetime.date.today()
        recurring.save(update_fields=["is_active", "end_date"])
        messages.success(self.request, "Recurring transaction deactivated.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("budget:recurring-list", kwargs={"budget_pk": self.budget.pk})
