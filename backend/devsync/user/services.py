from random import randint

from django.core.mail import send_mail

from config import settings


def generate_verification_code() -> str:
    return str(randint(100000, 999999))


def send_email(title, message, user_email: str):
    send_mail(
        title,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )

