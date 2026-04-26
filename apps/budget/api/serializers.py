from decimal import Decimal

from django.db import transaction as db_transaction
from rest_framework import serializers

from apps.budget.models import Budget, BudgetMembership, Category, CategoryBudget, PaymentMethod, RecurringTransaction, Transaction, TransactionLine


class PaymentMethodSerializer(serializers.ModelSerializer):
    payment_type_display = serializers.CharField(source="get_payment_type_display", read_only=True)

    class Meta:
        model = PaymentMethod
        fields = ["id", "name", "payment_type", "payment_type_display", "last_four", "is_active"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "category_type"]


class TransactionLineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_type = serializers.CharField(source="category.category_type", read_only=True)

    class Meta:
        model = TransactionLine
        fields = ["id", "category", "category_name", "category_type", "amount", "description"]


class TransactionSerializer(serializers.ModelSerializer):
    lines = TransactionLineSerializer(many=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    transaction_type = serializers.CharField(read_only=True)
    payment_method_name = serializers.CharField(source="payment_method.__str__", read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = [
            "id", "description", "due_date", "paid_date", "is_paid",
            "notes", "recurring", "payment_method", "payment_method_name",
            "lines", "total_amount", "transaction_type", "created_at",
        ]
        read_only_fields = ["recurring", "created_at"]

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("At least one line item is required.")
        types = {line["category"].category_type for line in lines}
        if len(types) > 1:
            raise serializers.ValidationError("All lines must be the same type (income or expense).")
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        with db_transaction.atomic():
            transaction = Transaction.objects.create(**validated_data)
            for line in lines_data:
                TransactionLine.objects.create(transaction=transaction, **line)
        return transaction

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        with db_transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if lines_data is not None:
                instance.lines.all().delete()
                for line in lines_data:
                    TransactionLine.objects.create(transaction=instance, **line)
        return instance


class BudgetMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.SerializerMethodField()
    gravatar_url = serializers.SerializerMethodField()

    class Meta:
        model = BudgetMembership
        fields = ["id", "user", "email", "name", "role", "gravatar_url", "joined_at"]
        read_only_fields = ["user", "joined_at"]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.email

    def get_gravatar_url(self, obj):
        return obj.user._get_gravatar_url()


class BudgetSerializer(serializers.ModelSerializer):
    members = BudgetMemberSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "members", "created_at"]
        read_only_fields = ["created_at"]


class DashboardSerializer(serializers.Serializer):
    """Computed summary for a budget month."""
    income_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    expense_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    income_by_category = serializers.ListField()
    expense_by_category = serializers.ListField()
    transactions = TransactionSerializer(many=True)
    upcoming_transactions = TransactionSerializer(many=True)


class RecurringTransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_type = serializers.CharField(source="category.category_type", read_only=True)
    next_due_date = serializers.SerializerMethodField()

    class Meta:
        model = RecurringTransaction
        fields = [
            "id", "name", "description", "amount", "category", "category_name", "category_type",
            "frequency", "interval", "start_date", "end_date", "is_active",
            "generated_through", "next_due_date", "created_at",
        ]
        read_only_fields = ["generated_through", "created_at"]

    def get_next_due_date(self, obj):
        import datetime
        if not obj.is_active:
            return None
        next_date = obj.next_due_date_after(datetime.date.today() - datetime.timedelta(days=1))
        return next_date.isoformat() if next_date else None


class CategoryBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryBudget
        fields = ["id", "category", "month", "assigned"]


class CategoryBudgetOverviewItemSerializer(serializers.Serializer):
    """One row in the budget overview grid."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    category_type = serializers.CharField()
    assigned = serializers.DecimalField(max_digits=12, decimal_places=2)
    activity = serializers.DecimalField(max_digits=12, decimal_places=2)
    available = serializers.DecimalField(max_digits=12, decimal_places=2)


class BudgetOverviewSerializer(serializers.Serializer):
    ready_to_assign = serializers.DecimalField(max_digits=12, decimal_places=2)
    income_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    expense_assigned = serializers.DecimalField(max_digits=12, decimal_places=2)
    categories = CategoryBudgetOverviewItemSerializer(many=True)


class MemberInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=BudgetMembership.ROLE_CHOICES, default=BudgetMembership.ROLE_MEMBER)
