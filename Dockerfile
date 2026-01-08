FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY digiplus_hr/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY digiplus_hr/ .

ENV DJANGO_SETTINGS_MODULE=digiplus_hr.settings

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "digiplus_hr.asgi:application"]
