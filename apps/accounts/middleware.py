from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        if request.user.is_authenticated:
            timezone.activate(ZoneInfo(request.user.timezone))
        else:
            timezone.deactivate()
