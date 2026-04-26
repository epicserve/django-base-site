import datetime

from apps.base.tests import BaseTest
from apps.budget.models import Budget, BudgetMembership, Category, RecurringTransaction, Transaction, TransactionLine


class TestBudgetMembership(BaseTest):
    def test_create_budget_adds_owner(self):
        user = self.make_user()
        budget = Budget.objects.create(created_by=user)
        BudgetMembership.objects.create(budget=budget, user=user, role=BudgetMembership.ROLE_OWNER)
        self.assertTrue(budget.members.filter(pk=user.pk).exists())

    def test_unique_membership(self):
        from django.db import IntegrityError

        user = self.make_user()
        budget = Budget.objects.create(created_by=user)
        BudgetMembership.objects.create(budget=budget, user=user, role=BudgetMembership.ROLE_OWNER)
        with self.assertRaises(IntegrityError):
            BudgetMembership.objects.create(budget=budget, user=user, role=BudgetMembership.ROLE_MEMBER)


class TestTransactionTotal(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = self.make_user()
        self.budget = Budget.objects.create(created_by=self.user)
        BudgetMembership.objects.create(budget=self.budget, user=self.user, role=BudgetMembership.ROLE_OWNER)
        self.cat = Category.objects.create(budget=self.budget, name="Food", category_type=Category.TYPE_EXPENSE)

    def test_total_amount_sums_lines(self):
        t = Transaction.objects.create(
            budget=self.budget,
            created_by=self.user,
            description="Groceries",
            due_date=datetime.date.today(),
        )
        TransactionLine.objects.create(transaction=t, category=self.cat, amount="50.00")
        TransactionLine.objects.create(transaction=t, category=self.cat, amount="30.00")
        self.assertEqual(t.total_amount, 80)

    def test_transaction_type_from_category(self):
        t = Transaction.objects.create(
            budget=self.budget,
            created_by=self.user,
            description="Groceries",
            due_date=datetime.date.today(),
        )
        TransactionLine.objects.create(transaction=t, category=self.cat, amount="50.00")
        self.assertEqual(t.transaction_type, Category.TYPE_EXPENSE)


class TestRecurringGeneration(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = self.make_user()
        self.budget = Budget.objects.create(created_by=self.user)
        BudgetMembership.objects.create(budget=self.budget, user=self.user, role=BudgetMembership.ROLE_OWNER)
        self.cat = Category.objects.create(budget=self.budget, name="Rent", category_type=Category.TYPE_EXPENSE)

    def test_generate_monthly_instances(self):
        start = datetime.date(2026, 1, 1)
        rt = RecurringTransaction.objects.create(
            budget=self.budget,
            category=self.cat,
            created_by=self.user,
            name="Monthly Rent",
            amount="1000.00",
            frequency=RecurringTransaction.FREQ_MONTHLY,
            start_date=start,
        )
        through = datetime.date(2026, 3, 31)
        created = rt.generate_instances_up_to(through)
        self.assertEqual(len(created), 3)  # Jan, Feb, Mar
        due_dates = list(Transaction.objects.filter(recurring=rt).values_list("due_date", flat=True).order_by("due_date"))
        self.assertEqual(due_dates[0], datetime.date(2026, 1, 1))
        self.assertEqual(due_dates[1], datetime.date(2026, 2, 1))
        self.assertEqual(due_dates[2], datetime.date(2026, 3, 1))

    def test_generate_annually_instances(self):
        start = datetime.date(2025, 6, 15)
        rt = RecurringTransaction.objects.create(
            budget=self.budget,
            category=self.cat,
            created_by=self.user,
            name="Annual Insurance",
            amount="500.00",
            frequency=RecurringTransaction.FREQ_ANNUALLY,
            start_date=start,
        )
        through = datetime.date(2027, 12, 31)
        created = rt.generate_instances_up_to(through)
        self.assertEqual(len(created), 3)  # Jun 2025, Jun 2026, Jun 2027

    def test_idempotent_generation(self):
        start = datetime.date(2026, 1, 1)
        rt = RecurringTransaction.objects.create(
            budget=self.budget,
            category=self.cat,
            created_by=self.user,
            name="Monthly Rent",
            amount="1000.00",
            frequency=RecurringTransaction.FREQ_MONTHLY,
            start_date=start,
        )
        through = datetime.date(2026, 3, 31)
        rt.generate_instances_up_to(through)
        rt.generate_instances_up_to(through)  # second call — no duplicates
        count = Transaction.objects.filter(recurring=rt).count()
        self.assertEqual(count, 3)
