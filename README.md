Got it! Here’s the **clean, updated README** focusing only on **single `.env`** and **two Docker Compose files** for dev and prod, without repeating full Dockerfile or nginx configs:

---

# NMS Project - Deployment & Local Setup

This guide explains how to run **NMS** locally and on **AWS EC2** using Docker.

---

## 1️⃣ Prerequisites

* Docker & Docker Compose installed
* AWS EC2 instance (for production)
* `.env` file with configuration

---

## 2️⃣ Environment Variables

Create a single `.env` file in the project root:

```env
HOST_URL=http://localhost       # Change to EC2 IP in prod
FRONTEND_PORT=3000
BACKEND_PORT=8000
DJANGO_SECRET_KEY=<your-secret-key>
DEBUG=True                       # Set False in prod
ALLOWED_HOSTS=localhost,127.0.0.1   # Set EC2 IP in prod
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
AZURE_REDIRECT_URI=${HOST_URL}:${BACKEND_PORT}/oauth2/callback/
POST_LOGOUT_REDIRECT_URI=${HOST_URL}:${BACKEND_PORT}/
CORS_ALLOWED_ORIGINS=${HOST_URL}:${FRONTEND_PORT}
CSRF_TRUSTED_ORIGINS=${HOST_URL}:${FRONTEND_PORT}
CORS_ALLOW_CREDENTIALS=True
REACT_APP_AZURE_CLIENT_ID=<your-client-id>
REACT_APP_AZURE_TENANT_ID=<your-tenant-id>
REACT_APP_REDIRECT_URI=${HOST_URL}:${FRONTEND_PORT}/oauth2/callback/
REACT_APP_SCOPES=openid profile email offline_access User.Read
REACT_APP_API_BASE_URL=${HOST_URL}:${BACKEND_PORT}/api
```

> Change `HOST_URL`, ports, and credentials for production.

---

## 3️⃣ Docker Compose Files

### Development (`docker-compose.dev.yml`)

* Backend: local dev, hot-reload
* Frontend: React dev server on `3000`
* Redis included

```bash
docker-compose -f docker-compose.dev.yml up --build
```

* Frontend: `http://localhost:3000`
* Backend: `http://localhost:8000`

---

### Production (`docker-compose.prod.yml`)

* Backend: Django via Gunicorn + Uvicorn
* Frontend: React build served by Nginx
* Redis included

```bash
docker-compose -f docker-compose.prod.yml up --build -d
docker-compose -f docker-compose.prod.yml logs -f
```

* Frontend: `http://<EC2_PUBLIC_IP>`
* Backend API proxied via Nginx `/api`
* Backend admin: `http://<EC2_PUBLIC_IP>/admin/`

---

## 4️⃣ Switching Between Dev and Prod

Single `.env` allows switching by **choosing compose file**:

```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Production
docker-compose -f docker-compose.prod.yml up --build -d
```

---

## 5️⃣ AWS EC2 Deployment Notes

1. Upload project via `scp`.
2. Install Docker & Docker Compose (Amazon Linux 2023).
3. Update `.env` for **EC2 IP** and set `DEBUG=False`.
4. Open ports **80, 443, 8000, 6379** in security group.
5. Run production compose:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

6. Optional: Setup HTTPS with Let’s Encrypt.

---

✅ This README now supports **single `.env`**, two separate compose files for dev/prod, and clear Docker build/run instructions.

---

If you want, I can also write a **one-liner command** to automatically switch between dev and prod with **environment variables**, so you don’t have to type two separate compose commands.

Do you want me to do that?
