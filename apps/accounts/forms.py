from allauth.account.forms import LoginForm
from allauth.utils import get_request_param
from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from django import forms
from django.contrib.auth import REDIRECT_FIELD_NAME


class SignInForm(LoginForm):
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
