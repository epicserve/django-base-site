from django.core.exceptions import PermissionDenied


class OwnerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.user != self.object.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
