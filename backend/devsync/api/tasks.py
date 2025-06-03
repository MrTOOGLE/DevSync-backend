from api.service import send_email
from config.celery import app


@app.task
def send_confirm_account_email(user_email: str):
    send_email(user_email)