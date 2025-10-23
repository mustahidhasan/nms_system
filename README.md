
---

# 🚀 Production Deployment Guide (Docker + Private/Public IP + HTTPS + Azure SSO)

---

## 1 Upload Project to Server

Copy your project folder or zip to the EC2 instance:

```bash
# Copy folder
scp -i your-key.pem -r /path/to/your/project ec2-user@3.90.164.200:~/nms

# Or copy zip
scp -i your-key.pem /path/to/nms.zip ec2-user@3.90.164.200:~/
```

Connect to the server:

```bash
ssh -i your-key.pem ec2-user@3.90.164.200
cd ~/
unzip nms.zip   # Only if uploaded as zip
cd nms
```

> Replace `3.90.164.200` with your **private or public IP** depending on your environment.

---

## 2 Install Docker & Docker Compose (Amazon Linux 2023)

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
ssh -i your-key.pem ec2-user@3.90.164.200
docker ps
```

Install Docker Compose:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 3 Configure `.env` Files for Production

There are **two `.env` files**:

1. **Backend `.env.prod.be`** → `nms/.env.prod.be`
2. **Frontend `.env.prod.fe`** → `nms/frontend/.env.prod.fe`

### Backend Example

```env
HOST_URL=https://3.90.164.200       # Use private or public IP
BACKEND_PORT=8000
DEBUG=False
ALLOWED_HOSTS=3.90.164.200,localhost
DJANGO_SECRET_KEY=your-secret-key

# Azure SSO redirect
AZURE_REDIRECT_URI=https://3.90.164.200:8000/oauth2/callback/
```

### Frontend Example

```env
REACT_APP_API_BASE_URL=https://3.90.164.200/api
REACT_APP_SCOPES=openid profile email offline_access User.Read
```

> Replace `3.90.164.200` with your instance’s IP (private or public depending on your setup).
> Ensure the SSL certificate CN matches this IP.

## 4 Build & Run Production Containers

Make the build script executable:

```bash
chmod +x build.sh
./build.sh prod
```

Check logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

---

## 5 Access the App

| Component     | URL                                          |
| ------------- | -------------------------------------------- |
| Frontend SPA  | `https://3.90.164.200/`                          |
| Backend Admin | `https://3.90.164.200/admin/login/?next=/admin/` |

> Browser will warn about the **self-signed SSL certificate**.
> Import the `.crt` into your system/browser if you want to remove the warning.

---

## 6 Azure SSO

* **Backend redirect URI**: `https://3.90.164.200:8000/oauth2/callback/`
* **Frontend scopes**: `openid profile email offline_access User.Read`

> Azure must be able to reach the IP — if using a **private IP**, only internal networks or VPN can access it.
> For external access, use a **public IP/domain or tunnel**.
