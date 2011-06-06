from django.conf import settings
from django.template import Context, loader


def server_error(request, template_name='500.html'):

    "Always includes STATIC_URL"
    from django.http import HttpResponseServerError

    # Use the 500 template for each program if it exists
    url_segment = request.path_info.strip("/").split("/")
    program_500_template = "%s/500.html" % url_segment[0]
    t = loader.select_template([program_500_template, '500.html'])

    return HttpResponseServerError(t.render(Context({'STATIC_URL': settings.MEDIA_URL})))
