from rest_framework import serializers
from .models import AdminUser


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["id", "email", "name", "phone", "company", "role", "avatar", "created_at"]
        read_only_fields = ["id", "created_at"]


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = AdminUser
        fields = ["email", "name", "phone", "company", "role", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = AdminUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
