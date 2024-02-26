from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.accounts.models import User
from apps.base.forms import NameForm


class NameChange(LoginRequiredMixin, generic.FormView):  # type: ignore
    form_class = NameForm
    template_name = "account/name_change.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = User.objects.get(pk=self.request.user.pk)  # type: ignore
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Your name was updated.")
        return reverse("account_change_name")
