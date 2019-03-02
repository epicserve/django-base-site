from rest_framework import routers

from apps.accounts import api

accounts_router = routers.SimpleRouter()
accounts_router.register(r'users', api.UserViewSet)
