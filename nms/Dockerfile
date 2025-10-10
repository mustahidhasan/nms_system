# -----------------------------
# Backend Dockerfile (nms/Dockerfile)
# -----------------------------
FROM python:3.12-slim

# -----------------------------
# Environment variables
# -----------------------------
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# -----------------------------
# System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping traceroute dnsutils mtr netcat-openbsd build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Python dependencies
# -----------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# -----------------------------
# Copy backend code
# -----------------------------
COPY . .

# -----------------------------
# Copy .env files into container
# -----------------------------
COPY .env.local .env.local
COPY .env.prod .env.prod

# -----------------------------
# Build argument to choose env
# -----------------------------
ARG ENV_FILE=.env.local
# Make sure the ARG is available at build time
RUN echo "Using environment file: ${ENV_FILE}" && cp ${ENV_FILE} .env

# -----------------------------
# Collect static files in production
# -----------------------------
RUN if [ "${ENV_FILE}" = ".env.prod" ]; then python manage.py collectstatic --noinput; fi

# -----------------------------
# Expose port
# -----------------------------
EXPOSE 8000

# -----------------------------
# Start ASGI server with Gunicorn + Uvicorn
# -----------------------------
CMD ["gunicorn", "nms.asgi:application", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]
