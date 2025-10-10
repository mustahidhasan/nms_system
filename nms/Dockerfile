# -----------------------------
# Backend Dockerfile (nms/Dockerfile)
# -----------------------------
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies including networking tools and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    traceroute \
    dnsutils \
    mtr \
    netcat-openbsd \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend code
COPY . .

# Collect static files for production if ENV_FILE=prod
ARG ENV_FILE
RUN if [ "$ENV_FILE" = "prod" ]; then python manage.py collectstatic --noinput; fi

# Expose Django port
EXPOSE 8000

# Start ASGI server with Gunicorn + Uvicorn
CMD ["gunicorn", "nms.asgi:application", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]
