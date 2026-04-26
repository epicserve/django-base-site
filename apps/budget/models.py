import calendar
import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum


class Budget(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_budgets",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="BudgetMembership",
        related_name="budgets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        names = ", ".join(
            m.get_full_name() or m.email
            for m in self.members.all()[:3]
        )
        return f"Budget ({names})" if names else f"Budget #{self.pk}"


class BudgetMembership(models.Model):
    ROLE_OWNER = "owner"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_MEMBER, "Member"),
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budget_memberships",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("budget", "user")]
        ordering = ["joined_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.budget} ({self.role})"


class Category(models.Model):
    TYPE_INCOME = "income"
    TYPE_EXPENSE = "expense"
    TYPE_CHOICES = [
        (TYPE_INCOME, "Income"),
        (TYPE_EXPENSE, "Expense"),
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_categories",
    )

    class Meta:
        unique_together = [("budget", "name", "category_type")]
        ordering = ["category_type", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_type_display()})"


class RecurringTransaction(models.Model):
    FREQ_MONTHLY = "monthly"
    FREQ_EVERY_N = "every_n_months"
    FREQ_ANNUALLY = "annually"
    FREQ_CHOICES = [
        (FREQ_MONTHLY, "Monthly"),
        (FREQ_EVERY_N, "Every N Months"),
        (FREQ_ANNUALLY, "Annually"),
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="recurring_transactions")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="recurring_transactions")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_recurring_transactions",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQ_CHOICES)
    interval = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of months between occurrences. Used only when frequency is 'Every N Months'.",
    )
    start_date = models.DateField(help_text="Date of the first occurrence.")
    end_date = models.DateField(null=True, blank=True, help_text="No new instances are generated after this date.")
    is_active = models.BooleanField(default=True)
    generated_through = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_frequency_display()})"

    def next_due_date_after(self, reference_date: datetime.date) -> datetime.date | None:
        """Return the next due date strictly after reference_date, or None if past end_date."""
        date = self.start_date
        while date <= reference_date:
            date = self._advance(date)
        if self.end_date and date > self.end_date:
            return None
        return date

    def _advance(self, date: datetime.date) -> datetime.date:
        """Advance date by one recurrence interval."""
        if self.frequency == self.FREQ_MONTHLY:
            months = 1
        elif self.frequency == self.FREQ_EVERY_N:
            months = self.interval
        else:  # annually
            months = 12
        month = date.month + months
        year = date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(date.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    def generate_instances_up_to(self, through_date: datetime.date) -> list["Transaction"]:
        """Generate Transaction instances up to through_date. Returns new instances created."""
        from apps.budget.models import Transaction

        start = self.generated_through if self.generated_through else self.start_date - datetime.timedelta(days=1)
        due = self.start_date if self.generated_through is None else None

        # Build all due dates in range
        due_dates: list[datetime.date] = []
        candidate = self.start_date
        while candidate <= through_date:
            if candidate > start:
                if self.end_date is None or candidate <= self.end_date:
                    due_dates.append(candidate)
            candidate = self._advance(candidate)

        created: list[Transaction] = []
        for due_date in due_dates:
            transaction, is_new = Transaction.objects.get_or_create(
                recurring=self,
                due_date=due_date,
                defaults={
                    "budget": self.budget,
                    "created_by": self.created_by,
                    "description": self.name,
                    "is_paid": False,
                },
            )
            if is_new:
                created.append(transaction)

        if due_dates:
            self.generated_through = due_dates[-1]
            self.save(update_fields=["generated_through"])

        return created


class Transaction(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="transactions")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_transactions",
    )
    recurring = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instances",
    )
    payment_method = models.ForeignKey(
        "PaymentMethod",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    description = models.CharField(max_length=200)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self) -> str:
        return f"{self.description} — {self.due_date}"

    @property
    def total_amount(self) -> Decimal:
        result = self.lines.aggregate(total=Sum("amount"))["total"]
        if result is not None:
            return result
        # Recurring instances inherit amount from the template
        if self.recurring_id:
            return self.recurring.amount  # type: ignore[union-attr]
        return Decimal("0.00")

    @property
    def transaction_type(self) -> str:
        first_line = self.lines.select_related("category").first()
        if first_line:
            return first_line.category.category_type
        # Recurring instances inherit type from the template
        if self.recurring_id:
            return self.recurring.category.category_type  # type: ignore[union-attr]
        return ""


class PaymentMethod(models.Model):
    TYPE_CREDIT = "credit_card"
    TYPE_DEBIT = "debit_card"
    TYPE_CASH = "cash"
    TYPE_BANK = "bank_transfer"
    TYPE_OTHER = "other"
    TYPE_CHOICES = [
        (TYPE_CREDIT, "Credit Card"),
        (TYPE_DEBIT, "Debit Card"),
        (TYPE_CASH, "Cash"),
        (TYPE_BANK, "Bank Transfer"),
        (TYPE_OTHER, "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    name = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OTHER)
    last_four = models.CharField(max_length=4, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        suffix = f" ···{self.last_four}" if self.last_four else ""
        return f"{self.name}{suffix}"


class CategoryBudget(models.Model):
    """Monthly spending target assigned to a category."""

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="category_budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category_budgets")
    month = models.DateField(help_text="First day of the month this assignment applies to.")
    assigned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = [("budget", "category", "month")]
        ordering = ["month", "category__name"]

    def __str__(self) -> str:
        return f"{self.category.name} — {self.month:%Y-%m}: {self.assigned}"


class TransactionLine(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="lines")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transaction_lines")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["category__name"]

    def __str__(self) -> str:
        return f"{self.category.name}: {self.amount}"
