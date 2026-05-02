import io

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

import qrcode
import qrcode.image.svg


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


@require_GET
@login_required
def qr_svg(request):
    """
    Render a QR code as an inline SVG.

    Used by the SPA to display a TOTP enrollment QR code without depending
    on a third-party image service. Locked to authenticated users so the
    endpoint can't be used as an open QR generator.
    """
    data = request.GET.get("data", "")
    if not data or len(data) > 2048:
        return HttpResponseBadRequest("Missing or oversized 'data' query parameter.")
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    response = HttpResponse(buf.getvalue(), content_type="image/svg+xml")
    response["Cache-Control"] = "no-store"
    return response
