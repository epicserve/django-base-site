from django import forms
from django.contrib.auth import REDIRECT_FIELD_NAME

from allauth.account.forms import LoginForm
from allauth.utils import get_request_param
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit, Div


class SignInForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        redirect_field_value = get_request_param(self.request, REDIRECT_FIELD_NAME)
        if redirect_field_value:
            self.fields[REDIRECT_FIELD_NAME] = forms.Field(initial=redirect_field_value)
        
        # Add Tailwind classes to form fields
        self.fields['login'].widget.attrs.update({
            'class': 'appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white dark:bg-gray-800 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Email address'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white dark:bg-gray-800 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password'
        })
        
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Field("login"),
            Field("password"),
            Field("remember", css_class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"),
            Field(REDIRECT_FIELD_NAME, type="hidden"),
            FormActions(Submit(name="sign-in", value="Sign In", css_class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500")),
        )
