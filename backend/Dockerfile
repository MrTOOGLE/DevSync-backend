FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /backend_app

COPY requirements.txt /backend_app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /backend_app/