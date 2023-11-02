from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

import requests
from allauth.account import signals
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return getattr(settings, "ACCOUNT_SIGNUP_OPEN", True)

    def get_logout_redirect_url(self, request):
        domain = "dev-uqbp6t5o50e72kx7.us.auth0.com"
        auth0_logout_url = f"https://{domain}/v2/logout"
        token = request.session.get("socialaccount_token")
        if token:
            params = {"client_id": settings.AUTH0_CLIENT_ID}
            headers = {"Authorization": f"Bearer {token}"}
            requests.get(auth0_logout_url, headers=headers, params=params, timeout=30)

        logout(request)
        return "/"

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


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        request.session["socialaccount_token"] = sociallogin.token
