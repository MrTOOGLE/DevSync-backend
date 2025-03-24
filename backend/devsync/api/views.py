from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render

from config import settings


def index(request):
    return HttpResponse("Hello")


def send_test_mail(request):
    send_mail(
        "Test mail",
        "Test message",
        settings.EMAIL_HOST_USER,
        ["manin_nikita04@mail.ru"],
        fail_silently=False
    )
    return HttpResponse("Sent successfully")
