from django.http import HttpResponse
from django.shortcuts import render

from api.tasks import send_confirm_account_email
from config import settings


def index(request):
    return HttpResponse("Hello")


def send_test_mail(request):
    send_confirm_account_email.delay(settings.EMAIL_TEST_HOST_USER)
    return HttpResponse("Sent successfully")
