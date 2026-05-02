from django.urls import re_path

from . import views

app_name = "organizations"
urlpatterns = [
    re_path(r"^invite/(?P<key>[0-9a-z]+)/accept/$", views.AcceptInviteView.as_view(), name="accept_invite"),
]
