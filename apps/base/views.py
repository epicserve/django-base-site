from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render
from django.template import Context, loader
from django.urls import reverse
from django.views import generic

from .forms import NameForm


class NameChange(generic.FormView):
    form_class = NameForm
    template_name = 'account/name_change.html'

    def get_form_kwargs(self):
        kwargs = super(NameChange, self).get_form_kwargs()
        kwargs["instance"] = User.objects.get(pk=self.request.user.pk)
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(NameChange, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Your name was updated.')
        return reverse('account_change_name')


class IndexView(generic.TemplateView):
    template_name = 'index.html'


def http_500(request):
    raise Exception


def http_404(request):
    return render(request, '404.html')
