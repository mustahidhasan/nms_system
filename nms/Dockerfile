FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies for networking commands
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    traceroute \
    dnsutils \
    mtr \
    netcat-openbsd \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
    
# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend code
COPY . .

# Expose Django port
EXPOSE 8000

# Start ASGI server with Gunicorn + Uvicorn
CMD ["gunicorn", "nms.asgi:application", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]
