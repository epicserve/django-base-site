from django.contrib import admin

from apps.billing.models import BillingCustomer


@admin.register(BillingCustomer)
class BillingCustomerAdmin(admin.ModelAdmin):
    list_display = ("organization", "stripe_customer_id", "email", "created")
    search_fields = ("organization__name", "organization__slug", "stripe_customer_id", "email")
    readonly_fields = ("stripe_customer_id", "created", "modified")
