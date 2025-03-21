FROM python:3.12

ENV PYTHONPATH=/backend-app/devsync

WORKDIR /backend-app

COPY requirements.txt /backend-app/
COPY devsync /backend-app/devsync

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "devsync.config.wsgi:application"]