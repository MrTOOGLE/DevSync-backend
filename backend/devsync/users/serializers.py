from django.core.cache import cache
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from config import settings
from .models import User
from .services import generate_verification_code
from .tasks import send_verification_code_email


def validate_email(value):
    try:
        user = User.objects.get(email=value)
        if user.is_email_verified:
            raise ValidationError("This email is already verified.")
    except User.DoesNotExist:
        raise ValidationError("There is no user with this email.")
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
            raise serializers.ValidationError("There is no user with this email0.")


class ConfirmEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email])
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value):
        email = self.initial_data.get('email')
        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(username=email)
        cached_code = cache.get(code_cache_name)

        if not cached_code:
            raise ValidationError("Invalid verification code.")

        if cached_code != value:
            raise ValidationError("The code does not match.")

        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        user.verify_email()

        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(username=email)
        cache.delete(code_cache_name)
