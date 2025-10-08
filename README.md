---

# 🚀 NMS Project – Production Deployment (AWS EC2)

This guide explains how to deploy the **NMS** project to an **AWS EC2 instance** for production use.

---

## 🧩 1. Upload the project to the server

Use `scp` to copy your project folder (or zip) to the EC2 instance:

```bash
scp -i your-key.pem -r /path/to/your/project ec2-user@EC2_PUBLIC_IP:~/nms
```

> 🔸 Replace:
>
> * `your-key.pem` → your SSH key file
> * `/path/to/your/project` → local path to your NMS project
> * `EC2_PUBLIC_IP` → your instance public IP (e.g. `54.211.170.64`)

If you zipped the project instead:

```bash
scp -i your-key.pem /path/to/nms.zip ec2-user@EC2_PUBLIC_IP:~/
```

---

## 🔐 2. Connect to the EC2 instance

```bash
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
cd ~/
unzip nms.zip
cd nms
```

---

## 🐳 3. Install Docker and Docker Compose (Amazon Linux 2023)

```bash
# Update system packages
sudo dnf update -y

# Install Docker
sudo dnf install docker -y

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to Docker group (so you can run docker without sudo)
sudo usermod -aG docker ec2-user
```

Then **log out and reconnect** to apply group permissions:

```bash
exit
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
```

Now verify Docker works:

```bash
docker ps
```

---

### 🧰 Install Docker Compose v2

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## ⚙️ 4. Update the `.env` file (Production)

Inside your `nms` backend folder, configure the environment variables:

```env
# -----------------------------
# Django backend settings
# -----------------------------
DJANGO_SECRET_KEY=django-insecure-x2--wh#=1^e7n^k*kttuey@wt%a$a7@)c=$_7ybu31v&yg0
DEBUG=False
ALLOWED_HOSTS=54.211.170.64

# Azure AD credentials
AZURE_TENANT_ID=20873f24-587c-427a-8b39-20b75349b61d
AZURE_CLIENT_ID=f682b7c8-8047-4b0b-91de-f6735855f32d
AZURE_CLIENT_SECRET=e1~8Q~6pHm06y1Zoeu2t6U2b0ICe_rVF2WSMYaaQ

# Redirect URIs
AZURE_REDIRECT_URI=http://54.211.170.64/oauth2/callback/
POST_LOGOUT_REDIRECT_URI=http://54.211.170.64/

# -----------------------------
# CORS & CSRF
# -----------------------------
CORS_ALLOWED_ORIGINS=http://54.211.170.64
CSRF_TRUSTED_ORIGINS=http://54.211.170.64

# -----------------------------
# React frontend settings
# -----------------------------
REACT_APP_AZURE_CLIENT_ID=f682b7c8-8047-4b0b-91de-f6735855f32d
REACT_APP_AZURE_TENANT_ID=20873f24-587c-427a-8b39-20b75349b61d
REACT_APP_REDIRECT_URI=http://54.211.170.64/oauth2/callback/
REACT_APP_SCOPES=openid profile email offline_access User.Read
REACT_APP_API_BASE_URL=http://54.211.170.64/api
```

> 💡 Use `http://` unless you’ve configured SSL certificates for HTTPS.

---

## 🧱 5. Build and run Docker containers

```bash
cd ~/nms
docker-compose build --no-cache
docker-compose up -d
```

The app will now start in the background.
Check the running containers:

```bash
docker ps
```

View logs:

```bash
docker-compose logs -f
```

---

## 🌐 6. Configure EC2 Security Groups

In the AWS Console, edit your EC2 instance’s security group to allow:

| Port | Protocol | Purpose                 |
| ---- | -------- | ----------------------- |
| 80   | TCP      | HTTP (frontend/backend) |
| 443  | TCP      | HTTPS (if SSL used)     |
| 8000 | TCP      | Optional direct backend |

---

## ✅ 7. Access Your App

Open your browser and visit:

```
http://54.211.170.64
```

Your **NMS application** should now be live 🎉

---
