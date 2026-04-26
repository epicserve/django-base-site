import calendar
import datetime
from decimal import Decimal

from django.db.models import ProtectedError, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.budget.models import Budget, BudgetMembership, Category, CategoryBudget, PaymentMethod, RecurringTransaction, Transaction, TransactionLine
from apps.accounts.models import User

from .serializers import (
    BudgetMemberSerializer,
    BudgetOverviewSerializer,
    BudgetSerializer,
    CategoryBudgetSerializer,
    CategorySerializer,
    DashboardSerializer,
    MemberInviteSerializer,
    PaymentMethodSerializer,
    RecurringTransactionSerializer,
    TransactionSerializer,
)


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class BudgetAPIMixin:
    """Resolve self.budget from URL kwargs and verify membership."""

    budget: Budget

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # type: ignore[misc]
        budget_pk = kwargs.get("budget_pk")
        self.budget = get_object_or_404(Budget, pk=budget_pk)
        if not self.budget.members.filter(pk=request.user.pk).exists():
            from rest_framework.exceptions import NotFound
            raise NotFound


class BudgetOwnerAPIMixin(BudgetAPIMixin):
    """Restrict to budget owners only."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        is_owner = BudgetMembership.objects.filter(
            budget=self.budget, user=request.user, role=BudgetMembership.ROLE_OWNER
        ).exists()
        if not is_owner:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------


class BudgetDetailAPIView(BudgetAPIMixin, APIView):
    def get(self, request, budget_pk):
        serializer = BudgetSerializer(self.budget)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class DashboardAPIView(BudgetAPIMixin, APIView):
    def get(self, request, budget_pk):
        month_str = request.query_params.get("month")
        try:
            selected = datetime.date.fromisoformat(month_str + "-01") if month_str else datetime.date.today().replace(day=1)
        except (ValueError, TypeError, AttributeError):
            selected = datetime.date.today().replace(day=1)

        last_day = calendar.monthrange(selected.year, selected.month)[1]
        period_start = selected
        period_end = selected.replace(day=last_day)

        transactions = (
            Transaction.objects.filter(budget=self.budget, due_date__range=(period_start, period_end))
            .select_related("recurring__category")
            .prefetch_related("lines__category")
            .order_by("due_date")
        )

        income_lines = TransactionLine.objects.filter(
            transaction__budget=self.budget,
            transaction__due_date__range=(period_start, period_end),
            category__category_type=Category.TYPE_INCOME,
        )
        expense_lines = TransactionLine.objects.filter(
            transaction__budget=self.budget,
            transaction__due_date__range=(period_start, period_end),
            category__category_type=Category.TYPE_EXPENSE,
        )

        income_total = income_lines.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        expense_total = expense_lines.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        net_balance = income_total - expense_total

        income_by_category = list(
            income_lines.values("category__name").annotate(total=Sum("amount")).order_by("category__name")
        )
        expense_by_category = list(
            expense_lines.values("category__name").annotate(total=Sum("amount")).order_by("category__name")
        )

        today = datetime.date.today()
        upcoming = (
            Transaction.objects.filter(
                budget=self.budget, recurring__isnull=False, is_paid=False, due_date__gte=today
            )
            .prefetch_related("lines__category")
            .order_by("due_date")[:10]
        )

        data = {
            "income_total": income_total,
            "expense_total": expense_total,
            "net_balance": net_balance,
            "income_by_category": income_by_category,
            "expense_by_category": expense_by_category,
            "transactions": transactions,
            "upcoming_transactions": upcoming,
        }
        serializer = DashboardSerializer(data)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategoryListAPIView(BudgetAPIMixin, APIView):
    def get(self, request, budget_pk):
        categories = Category.objects.filter(budget=self.budget).order_by("category_type", "name")
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request, budget_pk):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(budget=self.budget, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailAPIView(BudgetAPIMixin, APIView):
    def _get_category(self, pk):
        return get_object_or_404(Category, pk=pk, budget=self.budget)

    def get(self, request, budget_pk, pk):
        serializer = CategorySerializer(self._get_category(pk))
        return Response(serializer.data)

    def put(self, request, budget_pk, pk):
        category = self._get_category(pk)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, budget_pk, pk):
        category = self._get_category(pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, budget_pk, pk):
        category = self._get_category(pk)
        try:
            category.delete()
        except ProtectedError:
            return Response(
                {"detail": "This category has transactions and cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class TransactionListAPIView(BudgetAPIMixin, APIView):
    def get(self, request, budget_pk):
        qs = Transaction.objects.filter(budget=self.budget).select_related("recurring__category").prefetch_related("lines__category")
        month_str = request.query_params.get("month")
        if month_str:
            try:
                month_start = datetime.date.fromisoformat(month_str + "-01")
                last_day = calendar.monthrange(month_start.year, month_start.month)[1]
                month_end = month_start.replace(day=last_day)
                qs = qs.filter(due_date__range=(month_start, month_end))
            except (ValueError, TypeError):
                pass
        type_filter = request.query_params.get("type")
        if type_filter in (Category.TYPE_INCOME, Category.TYPE_EXPENSE):
            qs = qs.filter(lines__category__category_type=type_filter).distinct()
        serializer = TransactionSerializer(qs.order_by("due_date"), many=True)
        return Response(serializer.data)

    def post(self, request, budget_pk):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(budget=self.budget, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionDetailAPIView(BudgetAPIMixin, APIView):
    def _get_transaction(self, pk):
        return get_object_or_404(Transaction.objects.prefetch_related("lines__category"), pk=pk, budget=self.budget)

    def get(self, request, budget_pk, pk):
        serializer = TransactionSerializer(self._get_transaction(pk))
        return Response(serializer.data)

    def put(self, request, budget_pk, pk):
        transaction = self._get_transaction(pk)
        serializer = TransactionSerializer(transaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, budget_pk, pk):
        transaction = self._get_transaction(pk)
        serializer = TransactionSerializer(transaction, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, budget_pk, pk):
        self._get_transaction(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransactionMarkPaidAPIView(BudgetAPIMixin, APIView):
    def post(self, request, budget_pk, pk):
        transaction = get_object_or_404(Transaction, pk=pk, budget=self.budget)
        transaction.is_paid = not transaction.is_paid
        transaction.paid_date = datetime.date.today() if transaction.is_paid else None
        transaction.save(update_fields=["is_paid", "paid_date"])
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Recurring Transactions
# ---------------------------------------------------------------------------


class RecurringListAPIView(BudgetAPIMixin, APIView):
    def get(self, request, budget_pk):
        qs = RecurringTransaction.objects.filter(budget=self.budget).select_related("category")
        serializer = RecurringTransactionSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, budget_pk):
        serializer = RecurringTransactionSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(budget=self.budget, created_by=request.user)
            # Generate instances up to 3 months ahead
            from django.conf import settings as django_settings
            lookahead = getattr(django_settings, "BUDGET_RECURRING_LOOKAHEAD_MONTHS", 3)
            today = datetime.date.today()
            year = today.year + (today.month + lookahead - 1) // 12
            month = (today.month + lookahead - 1) % 12 + 1
            through_date = today.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])
            instance.generate_instances_up_to(through_date)
            return Response(RecurringTransactionSerializer(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecurringDetailAPIView(BudgetAPIMixin, APIView):
    def _get_recurring(self, pk):
        return get_object_or_404(RecurringTransaction, pk=pk, budget=self.budget)

    def get(self, request, budget_pk, pk):
        recurring = self._get_recurring(pk)
        instances = (
            Transaction.objects.filter(recurring=recurring)
            .prefetch_related("lines__category")
            .order_by("due_date")
        )
        data = RecurringTransactionSerializer(recurring).data
        data["instances"] = TransactionSerializer(instances, many=True).data
        return Response(data)

    def put(self, request, budget_pk, pk):
        recurring = self._get_recurring(pk)
        serializer = RecurringTransactionSerializer(recurring, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, budget_pk, pk):
        recurring = self._get_recurring(pk)
        serializer = RecurringTransactionSerializer(recurring, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            if request.data.get("delete_future_unpaid"):
                today = datetime.date.today()
                Transaction.objects.filter(recurring=instance, is_paid=False, due_date__gt=today).delete()
                instance.generated_through = None
                instance.save(update_fields=["generated_through"])
                lookahead = 3
                year = today.year + (today.month + lookahead - 1) // 12
                month = (today.month + lookahead - 1) % 12 + 1
                through_date = today.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])
                instance.generate_instances_up_to(through_date)
            return Response(RecurringTransactionSerializer(instance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, budget_pk, pk):
        """Manually create a transaction instance for this recurring schedule."""
        recurring = self._get_recurring(pk)
        due_date_str = request.data.get("due_date")
        if not due_date_str:
            return Response({"due_date": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            due_date = datetime.date.fromisoformat(due_date_str)
        except ValueError:
            return Response({"due_date": ["Enter a valid date."]}, status=status.HTTP_400_BAD_REQUEST)
        description = request.data.get("description") or recurring.name
        txn = Transaction.objects.create(
            budget=self.budget,
            recurring=recurring,
            description=description,
            due_date=due_date,
            created_by=request.user,
        )
        # Re-fetch with recurring so total_amount/transaction_type resolve correctly
        txn = Transaction.objects.select_related("recurring__category").get(pk=txn.pk)
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)

    def delete(self, request, budget_pk, pk):
        recurring = self._get_recurring(pk)
        if request.query_params.get("delete_future_unpaid"):
            today = datetime.date.today()
            Transaction.objects.filter(recurring=recurring, is_paid=False, due_date__gt=today).delete()
        recurring.is_active = False
        recurring.end_date = datetime.date.today()
        recurring.save(update_fields=["is_active", "end_date"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Budget Overview (YNAB-style category grid)
# ---------------------------------------------------------------------------


class BudgetOverviewAPIView(BudgetAPIMixin, APIView):
    """
    Returns a per-category budget overview for the given month.

    Each category row has:
      assigned  — the target the user set in CategoryBudget
      activity  — sum of transaction lines in that category this month
      available — assigned - activity  (for expense) or just activity (for income)

    Top-level fields:
      income_total   — sum of all income activity
      expense_assigned — sum of all expense assigned amounts
      ready_to_assign  — income_total - expense_assigned
    """

    def get(self, request, budget_pk):
        month_str = request.query_params.get("month")
        try:
            selected = datetime.date.fromisoformat(month_str + "-01") if month_str else datetime.date.today().replace(day=1)
        except (ValueError, TypeError, AttributeError):
            selected = datetime.date.today().replace(day=1)

        last_day = calendar.monthrange(selected.year, selected.month)[1]
        period_start = selected
        period_end = selected.replace(day=last_day)

        # Activity per category for this month
        activity_qs = (
            TransactionLine.objects.filter(
                transaction__budget=self.budget,
                transaction__due_date__range=(period_start, period_end),
            )
            .values("category_id")
            .annotate(total=Sum("amount"))
        )
        activity_map: dict[int, Decimal] = {row["category_id"]: row["total"] for row in activity_qs}

        # Assigned amounts for this month
        assigned_qs = CategoryBudget.objects.filter(budget=self.budget, month=period_start).values("category_id", "assigned")
        assigned_map: dict[int, Decimal] = {row["category_id"]: row["assigned"] for row in assigned_qs}

        categories = Category.objects.filter(budget=self.budget).order_by("category_type", "name")

        rows = []
        income_total = Decimal("0.00")
        expense_assigned = Decimal("0.00")

        for cat in categories:
            activity = activity_map.get(cat.pk, Decimal("0.00"))
            assigned = assigned_map.get(cat.pk, Decimal("0.00"))
            if cat.category_type == Category.TYPE_INCOME:
                income_total += activity
                available = activity
            else:
                expense_assigned += assigned
                available = assigned - activity
            rows.append({
                "id": cat.pk,
                "name": cat.name,
                "category_type": cat.category_type,
                "assigned": assigned,
                "activity": activity,
                "available": available,
            })

        data = {
            "income_total": income_total,
            "expense_assigned": expense_assigned,
            "ready_to_assign": income_total - expense_assigned,
            "categories": rows,
        }
        serializer = BudgetOverviewSerializer(data)
        return Response(serializer.data)


class CategoryBudgetAPIView(BudgetAPIMixin, APIView):
    """Upsert the assigned amount for a category in a given month."""

    def put(self, request, budget_pk, category_pk):
        category = get_object_or_404(Category, pk=category_pk, budget=self.budget)
        month_str = request.data.get("month")
        if not month_str:
            return Response({"month": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            month = datetime.date.fromisoformat(month_str + "-01") if len(month_str) == 7 else datetime.date.fromisoformat(month_str)
        except (ValueError, TypeError):
            return Response({"month": ["Enter a valid YYYY-MM date."]}, status=status.HTTP_400_BAD_REQUEST)
        # Normalise to first of month
        month = month.replace(day=1)
        obj, _ = CategoryBudget.objects.update_or_create(
            budget=self.budget,
            category=category,
            month=month,
            defaults={"assigned": request.data.get("assigned", "0.00")},
        )
        return Response(CategoryBudgetSerializer(obj).data)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class MemberListAPIView(BudgetOwnerAPIMixin, APIView):
    def get(self, request, budget_pk):
        memberships = BudgetMembership.objects.filter(budget=self.budget).select_related("user")
        serializer = BudgetMemberSerializer(memberships, many=True)
        return Response(serializer.data)

    def post(self, request, budget_pk):
        serializer = MemberInviteSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            role = serializer.validated_data["role"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"email": [f"No account found for {email}."]}, status=status.HTTP_400_BAD_REQUEST)
            _, created = BudgetMembership.objects.get_or_create(
                budget=self.budget, user=user, defaults={"role": role}
            )
            if not created:
                return Response({"email": [f"{email} is already a member."]}, status=status.HTTP_400_BAD_REQUEST)
            membership = BudgetMembership.objects.select_related("user").get(budget=self.budget, user=user)
            return Response(BudgetMemberSerializer(membership).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemberDetailAPIView(BudgetOwnerAPIMixin, APIView):
    def delete(self, request, budget_pk, pk):
        membership = get_object_or_404(BudgetMembership, pk=pk, budget=self.budget)
        if membership.user == request.user:
            return Response({"detail": "You cannot remove yourself."}, status=status.HTTP_400_BAD_REQUEST)
        owner_count = BudgetMembership.objects.filter(budget=self.budget, role=BudgetMembership.ROLE_OWNER).count()
        if membership.role == BudgetMembership.ROLE_OWNER and owner_count <= 1:
            return Response({"detail": "Cannot remove the last owner."}, status=status.HTTP_400_BAD_REQUEST)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Payment Methods (user-scoped, no budget context needed)
# ---------------------------------------------------------------------------


class PaymentMethodListAPIView(APIView):
    def get(self, request):
        methods = PaymentMethod.objects.filter(user=request.user)
        return Response(PaymentMethodSerializer(methods, many=True).data)

    def post(self, request):
        serializer = PaymentMethodSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentMethodDetailAPIView(APIView):
    def _get(self, request, pk):
        return get_object_or_404(PaymentMethod, pk=pk, user=request.user)

    def patch(self, request, pk):
        method = self._get(request, pk)
        serializer = PaymentMethodSerializer(method, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self._get(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
