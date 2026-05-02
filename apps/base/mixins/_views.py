from django.contrib.auth.mixins import AccessMixin


class StaffRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a staff user."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_staff is False:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
