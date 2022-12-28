from django.urls import path

from apps.accounts.views import NameChange

app_name = "accounts"
urlpatterns = [
    path("name/", NameChange.as_view(), name="account_change_name"),
]
