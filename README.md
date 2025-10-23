* Private IP / public IP support
* HTTPS with self-signed SSL
* Dockerized React + Django + Nginx + Redis
* Azure SSO configuration

---

# 🚀 Production Deployment Guide (Docker + Private/Public IP + HTTPS + Azure SSO)

---

## 1️⃣ Upload Project to Server

Copy your project folder or zip to the EC2 instance:

```bash
# Copy folder
scp -i your-key.pem -r /path/to/your/project ec2-user@<EC2_IP>:~/nms

# Or copy zip
scp -i your-key.pem /path/to/nms.zip ec2-user@<EC2_IP>:~/
```

Connect to the server:

```bash
ssh -i your-key.pem ec2-user@<EC2_IP>
cd ~/
unzip nms.zip   # Only if uploaded as zip
cd nms
```

> Replace `<EC2_IP>` with your **private or public IP** depending on your environment.

---

## 2️⃣ Install Docker & Docker Compose (Amazon Linux 2023)

```bash
sudo dnf update -y
sudo dnf install docker -y
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
```

> Log out and reconnect for Docker group permissions:

```bash
exit
ssh -i your-key.pem ec2-user@<EC2_IP>
docker ps
```

Install Docker Compose:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 3️⃣ Configure `.env` Files for Production

There are **two `.env` files**:

1. **Backend `.env.prod.be`** → `nms/.env.prod.be`
2. **Frontend `.env.prod.fe`** → `nms/frontend/.env.prod.fe`

### Backend Example

```env
HOST_URL=https://<EC2_IP>       # Use private or public IP
BACKEND_PORT=8000
DEBUG=False
ALLOWED_HOSTS=<EC2_IP>,localhost
DJANGO_SECRET_KEY=your-secret-key

# Azure SSO redirect
AZURE_REDIRECT_URI=https://<EC2_IP>:8000/oauth2/callback/
```

### Frontend Example

```env
REACT_APP_API_BASE_URL=https://<EC2_IP>/api
REACT_APP_SCOPES=openid profile email offline_access User.Read
```

> Replace `<EC2_IP>` with your instance’s IP (private or public depending on your setup).
> Ensure the SSL certificate CN matches this IP.

---

## 4️⃣ Generate Self-Signed SSL Certificate [do it from the compose.yml directory]

```bash
mkdir -p ./certs
cd ./certs

sudo openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout selfsigned.key \
  -out selfsigned.crt \
  -subj "/CN=<EC2_IP>"
```

> Nginx will use these certs to serve HTTPS.

---

## 5️⃣ Make sure `docker-compose.yml` has the correct Nginx service

Make sure your `nginx` service mounts the React build, SSL certs, Nginx config, and Django static files:

```yaml
nginx:
  image: nms-frontend
  container_name: nginx
  ports:
    - "80:80"
    - "443:443"
  depends_on:
    - backend
    - frontend
  volumes:
    - ./frontend/build:/usr/share/nginx/html
    - ./nginx.conf:/etc/nginx/conf.d/default.conf
    - ./certs:/etc/ssl/private
    - ./staticfiles:/app/staticfiles
  restart: always
```

---

## 6️⃣ Make sure Nginx Config (`nginx.conf`) looks like this

Make sure your `nginx.conf` has:

* HTTP → HTTPS redirect
* React build serving
* Django `/api/` and `/admin/` proxying
* Gzip compression
* Security headers

**Example snippet**:

```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/ssl/private/selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/selfsigned.key;

    root /usr/share/nginx/html;
    index index.html;

    location /admin/ {
        proxy_pass http://backend:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    location /static-django/ {
        alias /app/staticfiles/;
    }

    location / {
        try_files $uri /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_min_length 256;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
}
```

---

## 7️⃣ Build & Run Production Containers

Make the build script executable:

```bash
chmod +x build.sh
./build.sh prod
```

Check logs:

```bash
docker-compose logs -f
```

---

## 8️⃣ Access the App

| Component     | URL                                          |
| ------------- | -------------------------------------------- |
| Frontend SPA  | `https://<EC2_IP>/`                          |
| Backend Admin | `https://<EC2_IP>/admin/login/?next=/admin/` |

> Browser will warn about the **self-signed SSL certificate**.
> Import the `.crt` into your system/browser if you want to remove the warning.

---

## 9️⃣ Azure SSO

* **Backend redirect URI**: `https://<EC2_IP>:8000/oauth2/callback/`
* **Frontend scopes**: `openid profile email offline_access User.Read`

> Azure must be able to reach the IP — if using a **private IP**, only internal networks or VPN can access it.
> For external access, use a **public IP/domain or tunnel**.

---

✅ This updated guide works for **private IP, public IP, Dockerized React + Django + Nginx + Redis**, with **HTTPS and Azure SSO**.

---
