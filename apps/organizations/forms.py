from django import forms

from .models import Organization, OrganizationMember
from .session import save_counts


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ("name", "slug")

    def __init__(self, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(**kwargs)

    def save(self, commit=True):
        if self.instance.pk is None:
            instance = super().save(commit=True)
            OrganizationMember.objects.create(organization=instance, user=self.request.user, is_owner=True)
            save_counts(self.request)
            return instance

        return super().save(commit=True)
