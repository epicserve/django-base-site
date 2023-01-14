from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect

from allauth.account import signals
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return getattr(settings, "ACCOUNT_SIGNUP_OPEN", True)

    def post_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url):
        # Copied form https://github.com/pennersr/django-allauth/blob/master/allauth/account/adapter.py#L441 in order
        # to remove the "logged in" message. See this issue for more information: https://github.com/pennersr/django-allauth/issues/3205
        from allauth.account.utils import get_login_redirect_url

        response = HttpResponseRedirect(get_login_redirect_url(request, redirect_url, signup=signup))

        if signal_kwargs is None:
            signal_kwargs = {}
        signals.user_logged_in.send(
            sender=user.__class__,
            request=request,
            response=response,
            user=user,
            **signal_kwargs,
        )

        if getattr(settings, "ACCOUNT_SHOW_POST_LOGIN_MESSAGE", True) is True:
            self.add_message(
                request,
                messages.SUCCESS,
                "account/messages/logged_in.txt",
                {"user": user},
            )

        return response
