from django.core.cache import cache
from djoser.serializers import TokenCreateSerializer as BaseTokenCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied

from config import settings
from .models import User
from .services import generate_verification_code
from .tasks import send_verification_code_email


def validate_email(value):
    try:
        user = User.objects.get(email=value)
        if user.is_email_verified:
            raise ValidationError("Данный email уже подтвержден.")
    except User.DoesNotExist:
        raise ValidationError("Нет пользователя с таким email.")
    return value


class SendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email])

    def save(self):
        email = self.validated_data['email']
        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(username=email)
        cached_code = cache.get(code_cache_name)

        if not cached_code:
            cached_code = generate_verification_code()
            cache.set(code_cache_name, cached_code, settings.EMAIL_VERIFICATION_CODE_LIFETIME)

        try:
            user = User.objects.get(email=email)
            send_verification_code_email.delay(
                user.first_name,
                user.last_name,
                cached_code,
                user.email,
            )
        except User.DoesNotExist:
            raise serializers.ValidationError("Нет пользователя с таким email.")


class ConfirmEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email])
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value):
        email = self.initial_data.get('email')
        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(username=email)
        cached_code = cache.get(code_cache_name)

        if not cached_code:
            raise ValidationError("Недействительный код верификации.")

        if cached_code != value:
            raise ValidationError("Коды не совпадают.")

        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        user.verify_email()

        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(username=email)
        cache.delete(code_cache_name)


class TokenCreateSerializer(BaseTokenCreateSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        if not user.is_email_verified:
            raise PermissionDenied("Email не подтвержден. Пожалуйста, подтвердите ваш email перед входом.")

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'city', 'avatar')
        read_only_fields = ['id', 'email']

    def validate_email(self, value):
        if self.instance and self.instance.email != value:
            raise serializers.ValidationError("Изменение email запрещено")
        return value
