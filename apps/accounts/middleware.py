import base64
import binascii

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_str


class BasicAuthenticationMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        if "HTTP_AUTHORIZATION" in request.META:
            auth_parts = request.META.get("HTTP_AUTHORIZATION", "").split()
            auth_error = "Unauthorized"

            if not auth_parts or len(auth_parts) != 2 or auth_parts[0].lower() != "basic":
                return JsonResponse({"error": "Unauthorized"}, status=401)
            else:
                username_password = smart_str(auth_parts[1])
                try:
                    username_password = base64.b64decode(username_password).decode("utf8")
                    username, password = username_password.split(":", 1)
                    user = authenticate(request, username=username, password=password)
                except binascii.Error:
                    auth_error = (
                        "Invalid basic header: Username and password must be base64 encoded with a colon delimiter "
                        "(e.g. 'username:password')."
                    )
                    user = None

                if user is not None:
                    request.user = user
                else:
                    return JsonResponse({"error": auth_error}, status=401)
