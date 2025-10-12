FROM python:3.12-slim

ARG HOST_IP
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST_IP=${HOST_IP}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping traceroute dnsutils mtr netcat-openbsd build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "nms.asgi:application", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]
