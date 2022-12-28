from django.shortcuts import render
from django.views import generic


class IndexView(generic.TemplateView):
    template_name = "index.html"


def http_500(request):
    raise Exception


def http_404(request):
    return render(request, "404.html")
