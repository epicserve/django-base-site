from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template import Context, loader
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


def server_error(request):
    "Always includes STATIC_URL"
    from django.http import HttpResponseServerError

    # Use the 500 template for each program if it exists
    url_segment = request.path_info.strip("/").split("/")
    program_500_template = "%s/500.html" % url_segment[0]
    t = loader.select_template([program_500_template, '500.html'])

    return HttpResponseServerError(t.render(Context({'STATIC_URL': settings.MEDIA_URL})))
