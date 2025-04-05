from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from config import settings
from config.celery import app


@app.task
def send_verification_code_email(user_first_name: str, user_last_name: str, verification_code: str, user_email: str):
    message = EmailMultiAlternatives(
        subject=settings.EMAIL_VERIFICATION_SUBJECT,
        to=[user_email]
    )

    html_message = render_to_string(
        "user/email_verification.html",
        {
            "username": f"{user_last_name} {user_first_name}",
            "verification_code": verification_code
        },
    )
    message.attach_alternative(html_message, "text/html")
    message.send()
