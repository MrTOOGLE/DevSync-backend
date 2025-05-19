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
            raise ValidationError(
                "Данный email уже подтвержден.",
                code="email_already_verified"
            )
    except User.DoesNotExist:
        raise ValidationError(
            "Нет пользователя с таким email.",
            code="no_user"
        )
    return value


class SendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email])

    def save(self):
        email = self.validated_data['email']
        code_cache_name = settings.VERIFICATION_CODE_CACHE_KEY.format(username=email)
        cached_code = cache.get(code_cache_name)

        if not cached_code:
            cached_code = generate_verification_code()
            cache.set(code_cache_name, cached_code, settings.EMAIL_VERIFICATION_CODE_LIFETIME)

        try:
            user = User.objects.get(email=email)
            send_verification_code_email.delay(
                user.get_full_name(),
                cached_code,
                user.email,
            )
        except User.DoesNotExist:
            raise ValidationError(
                {"email": "Нет пользователя с таким email."},
                code="no_user"
            )


class ConfirmEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email])
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value):
        email = self.initial_data.get('email')
        code_cache_name = settings.VERIFICATION_CODE_CACHE_KEY.format(username=email)
        cached_code = cache.get(code_cache_name)

        if not cached_code:
            raise ValidationError(
                "Недействительный код верификации.",
                code="invalid_code"
            )

        if cached_code != value:
            raise ValidationError(
                "Недействительный код верификации.",
                code="invalid_code"
            )

        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        user.verify_email()

        code_cache_name = settings.VERIFICATION_CODE_CACHE_KEY.format(username=email)
        cache.delete(code_cache_name)


class TokenCreateSerializer(BaseTokenCreateSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        if not user.is_email_verified:
            raise PermissionDenied(
                {"email": "Аккаунт не подтвержден. Пожалуйста, подтвердите ваш email перед входом."},
                "email_is_not_verified"
            )

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'city', 'avatar')
        read_only_fields = ['id', 'email']
        extra_kwargs = {
            "first_name": {"trim_whitespace": True},
            "last_name": {"trim_whitespace": True},
            "city": {"trim_whitespace": True},
        }