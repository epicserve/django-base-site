from django import forms

from allauth.account.forms import SignupForm


class SignUpForm(SignupForm):
    """Headless allauth signup form with hidden timezone field populated by the SPA."""

    timezone = forms.CharField(widget=forms.HiddenInput, required=False)

    def save(self, request):
        user = super().save(request)
        if self.cleaned_data.get("timezone"):
            user.timezone = self.cleaned_data["timezone"]
            user.save(update_fields=["timezone"])
        return user
