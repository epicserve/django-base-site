from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie


class IndexView(generic.TemplateView):
    template_name = "index.html"


class SPAView(generic.TemplateView):
    template_name = "layouts/spa_shell.html"

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return ensure_csrf_cookie(view)


def http_500(request):
    raise Exception


def http_404(request):
    return render(request, "404.html")
