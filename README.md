
---

## 🟢 Production Deployment (AWS EC2)

This guide explains how to deploy the **NMS** project on an **AWS EC2 instance**.

---

### 1️⃣ Upload Project to EC2

Use `scp` to copy your project folder (or zip) to the EC2 instance:

```bash
scp -i your-key.pem -r /path/to/your/project ec2-user@EC2_PUBLIC_IP:~/nms
```

> Replace:
>
> * `your-key.pem` → your SSH key file
> * `/path/to/your/project` → local path to your NMS project
> * `EC2_PUBLIC_IP` → your instance public IP

If you zipped the project:

```bash
scp -i your-key.pem /path/to/nms.zip ec2-user@EC2_PUBLIC_IP:~/
```

---

### 2️⃣ Connect to EC2

```bash
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
cd ~/
unzip nms.zip   # Only if uploaded as zip
cd nms
```

---

### 3️⃣ Install Docker & Docker Compose (Amazon Linux 2023)

```bash
sudo dnf update -y
sudo dnf install docker -y
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
```

> Log out and reconnect to apply Docker group permissions:

```bash
exit
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
docker ps
```

Install Docker Compose:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

### 4️⃣ Configure `.env`

Use a **single `.env` file** for both local and production. Update only the `HOST_URL` and `ALLOWED_HOSTS` for production:

```env
# -----------------------------
# Host & ports
# -----------------------------
HOST_URL=http://54.211.170.64    # <- Update this to EC2 IP for production
FRONTEND_PORT=80
BACKEND_PORT=8000

# -----------------------------
# Django backend settings
# -----------------------------
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=54.211.170.64     # <- Update this to EC2 IP for production

# Azure AD credentials
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>

# Redirect URIs
AZURE_REDIRECT_URI=${HOST_URL}/oauth2/callback/
POST_LOGOUT_REDIRECT_URI=${HOST_URL}/

# -----------------------------
# CORS & CSRF
# -----------------------------
CORS_ALLOWED_ORIGINS=${HOST_URL}
CSRF_TRUSTED_ORIGINS=${HOST_URL}

# -----------------------------
# React frontend settings
# -----------------------------
REACT_APP_AZURE_CLIENT_ID=<your-client-id>
REACT_APP_AZURE_TENANT_ID=<your-tenant-id>
REACT_APP_REDIRECT_URI=${HOST_URL}/oauth2/callback/
REACT_APP_SCOPES=openid profile email offline_access User.Read
REACT_APP_API_BASE_URL=http://backend:8000/api
```

> For local development, set `HOST_URL=http://localhost` and `ALLOWED_HOSTS=localhost,127.0.0.1`.

---

### 5️⃣ Build & Run Docker Containers

**Local Development:**

```bash
docker-compose -f docker-compose.dev.yml up --build -d
```

**Production (AWS EC2):**

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Check logs:

```bash
docker-compose logs -f
```

---

### 6️⃣ Access the App

**Frontend (React):**

```
Local: http://localhost:3000
Production: http://54.211.170.64/
```

**Backend Admin:**

```
Local: http://localhost:8000/admin/
Production: http://54.211.170.64/admin/
```

> React communicates with backend via Docker network (`http://backend:8000/api`).

---

### ⚡ Notes

* For HTTPS, configure Nginx + Let’s Encrypt and update `.env` accordingly.
* Ensure EC2 **security group** allows ports: 80, 443, 8000, 6379.
* For production, consider **PostgreSQL/MySQL** instead of SQLite.
* `.env` file now controls both local and production; only `HOST_URL` and `ALLOWED_HOSTS` need changes.

---

