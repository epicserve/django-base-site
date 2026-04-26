from django.contrib import admin

from apps.budget.models import Budget, BudgetMembership, Category, RecurringTransaction, Transaction, TransactionLine


class BudgetMembershipInline(admin.TabularInline):
    model = BudgetMembership
    extra = 0


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_by", "created_at"]
    inlines = [BudgetMembershipInline, CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "category_type", "budget"]
    list_filter = ["category_type", "budget"]


class TransactionLineInline(admin.TabularInline):
    model = TransactionLine
    extra = 1


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["description", "due_date", "is_paid", "budget", "recurring"]
    list_filter = ["is_paid", "budget"]
    inlines = [TransactionLineInline]


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ["name", "frequency", "amount", "start_date", "end_date", "is_active", "budget"]
    list_filter = ["frequency", "is_active", "budget"]
