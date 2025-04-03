from rest_framework import serializers


class EmailVerificationCodeSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
