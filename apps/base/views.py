import json

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from maintenance_mode.core import set_maintenance_mode


class IndexView(generic.TemplateView):
    template_name = "index.html"


def http_500(request):
    raise Exception


def http_404(request):
    return render(request, "404.html")


class ToggleMaintenanceModeView(UserPassesTestMixin, generic.View):
    raise_exception = True
    # curl -X POST -H "Content-Type: application/json" -d '{"maintenance_mode": "off"}' -u "email:password" http://127.0.0.1:8000/maintenance-mode/

    def test_func(self):
        return self.request.user.is_superuser

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        enabled = data.get("enabled", None)
        if enabled is None or isinstance(enabled, bool) is False:
            return JsonResponse({"error": "Invalid request body. The 'enabled' field must be a boolean."}, status=400)

        set_maintenance_mode(enabled)
        return JsonResponse({"status": f"Maintenance mode is now {'enabled' if enabled is True else 'disabled'}."})
