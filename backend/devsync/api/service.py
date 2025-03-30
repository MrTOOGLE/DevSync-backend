from django.core.mail import send_mail

from config import settings


def send_email(user_email: str):
    send_mail(
        'Подтвердите почту для аккаунта Devsync',
        'Для подтверждения тыкнете на ссылку: http:/devsync.ru',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )