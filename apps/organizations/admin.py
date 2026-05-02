from django.contrib import admin

from .models import Organization, OrganizationMember


class MemberInline(admin.TabularInline):
    model = OrganizationMember


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [MemberInline]
    prepopulated_fields = {"slug": ("name",)}
