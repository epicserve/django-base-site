from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "email", "is_staff")
