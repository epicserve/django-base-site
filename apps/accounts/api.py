# ViewSets define the view behavior.
from rest_framework import viewsets

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
