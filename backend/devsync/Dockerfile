FROM python:3.12

SHELL ["/bin/bash", "-c"]

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt update && apt -qy install gcc libjpeg-dev libxslt-dev \
    libpq-dev libmariadb-dev libmariadb-dev-compat gettext cron openssh-client flake8 locales vim && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash appuser && \
    mkdir -p /backend/static /backend/media && \
    chown -R appuser:appuser /backend

WORKDIR /backend

COPY --chown=appuser:appuser .. .

RUN pip install --upgrade pip && pip install -r requirements.txt

USER appuser
