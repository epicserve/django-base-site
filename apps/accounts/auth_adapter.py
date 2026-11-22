from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect

from allauth.account import signals
from allauth.account.adapter import DefaultAccountAdapter
from allauth.core import context as allauth_context

from apps.base.utils.email import queue_email


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return getattr(settings, "ACCOUNT_SIGNUP_OPEN", True)

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        """
        Queue allauth's emails for a Celery worker, like `apps.base.utils.email.send_email`.

        Then a mail server that's down can't fail a signup, a password reset, or anything else that sends a
        verification code or security notice. This is allauth's `DefaultAccountAdapter.send_mail` with
        `queue_email()` in place of `msg.send()`; check it still matches after upgrading django-allauth.
        """
        request = allauth_context.request
        ctx = {
            "request": request,
            "email": email,
            "current_site": get_current_site(request),
        }
        ctx.update(context)
        queue_email(self.render_mail(template_prefix, email, ctx))

    def post_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url):
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
