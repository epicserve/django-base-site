from django import forms
from django.contrib.auth import REDIRECT_FIELD_NAME

from allauth.account.forms import LoginForm, SignupForm
from allauth.utils import get_request_param
from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit


class SignInForm(LoginForm):
    """Bootstrap-styled login form. Removed in Phase 2 along with the legacy template-based auth UI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        redirect_field_value = get_request_param(self.request, REDIRECT_FIELD_NAME)
        if redirect_field_value:
            self.fields[REDIRECT_FIELD_NAME] = forms.Field(initial=redirect_field_value)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("login"),
            FloatingField("password"),
            Field("remember"),
            Field(REDIRECT_FIELD_NAME, type="hidden"),
            FormActions(Submit(name="sign-in", value="Sign In", css_class="btn btn-primary w-100 py-2")),
        )


class SignUpForm(SignupForm):
    """Headless allauth signup form with hidden timezone field populated by the SPA."""

    timezone = forms.CharField(widget=forms.HiddenInput, required=False)

    def save(self, request):
        user = super().save(request)
        if self.cleaned_data.get("timezone"):
            user.timezone = self.cleaned_data["timezone"]
            user.save(update_fields=["timezone"])
        return user
