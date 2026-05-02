from django.contrib import messages
from django.shortcuts import redirect
from django.views import generic

from allauth.account.forms import SignupForm

from .models import OrganizationInvite, OrganizationMember
from .session import save_counts


class AcceptInviteView(generic.TemplateView):
    invite = None
    already_member_message = (
        "You're already a member of the {organization} organization."
        " Please sign in as a different user to use this invite."
    )

    def get_invite(self, key):
        if self.invite is None:
            self.invite = OrganizationInvite.objects.filter(key=key).first()

        return self.invite

    def get_signup_form(self):
        kwargs = {}
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        return SignupForm(**kwargs)

    def post(self, request, **kwargs):
        self.get_invite(kwargs["key"])
        redirect_url = "/"

        if self.invite is None:
            return redirect(request.path)

        if request.user.is_authenticated is False:
            form = self.get_signup_form()
            if form.is_valid() is False:
                context = self.get_context_data(**kwargs)
                context["form"] = form
                return super().render_to_response(context)
            else:
                try:
                    request.user = form.save(request)
                except ValueError:
                    form.add_error("email", "A user is already registered with this email address.")
                    context = self.get_context_data(**kwargs)
                    context["form"] = form
                    return super().render_to_response(context)

        if request.POST.get("decline") == "1":
            message = (
                f"You've canceled {self.invite.sender.get_full_name()}'s invitation to {self.invite.organization}."
            )
        else:
            if self.invite.organization.is_member(request.user) is True:
                messages.error(request, self.already_member_message.format(organization=self.invite.organization))
                return redirect(self.invite.accept_invite_url)
            message = (
                f"You've accepted {self.invite.sender.get_full_name()}'s invitation to {self.invite.organization}."
            )
            OrganizationMember.objects.get_or_create(
                organization=self.invite.organization, user=request.user, is_owner=self.invite.is_owner
            )
            save_counts(request)

        messages.success(request, message)
        self.invite.delete()
        return redirect(redirect_url)

    def get_template_names(self):
        if self.invite is None or self.invite and self.invite.is_expired:
            return ["organizations/invite_accept_invalid_or_expired.html"]
        elif self.request.user.is_authenticated is False:
            return ["organizations/invite_accept_for_anonymous_user.html"]
        else:
            return ["organizations/invite_accept_for_user.html"]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.get_invite(kwargs["key"])
        data["invite"] = self.invite
        data["already_member_message"] = None
        if (
            self.request.user.is_authenticated is True
            and self.invite
            and self.invite.organization.is_member(self.request.user) is True
        ):
            data["already_member_message"] = self.already_member_message.format(organization=self.invite.organization)
        if self.request.user.is_authenticated is False:
            data["form"] = self.get_signup_form()
        return data
