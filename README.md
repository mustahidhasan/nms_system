## 1️⃣ Upload Project to Server

Use `scp` to copy your project folder (or zip) to the server:

```bash
scp -i your-key.pem -r /path/to/your/project ec2-user@EC2_PUBLIC_IP:~/nms
```

> Or upload a zip:

```bash
scp -i your-key.pem /path/to/nms.zip ec2-user@EC2_PUBLIC_IP:~/
```

Connect to the server:

```bash
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
cd ~/
unzip nms.zip   # Only if uploaded as zip
cd nms
```

---

## 2️⃣ Install Docker & Docker Compose (Amazon Linux 2023)

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

## 3️⃣ Configure `.env` Files for Production

There are **two `.env` files**:

1. **Backend `.env.prod.be`** → located at `nms/`
2. **Frontend `.env.prod.fe`** → located at `nms/frontend/`

### **Backend example (`nms/.env.prod.be`)**

```env
HOST_URL=http://54.242.248.245
BACKEND_PORT=8000
DEBUG=False
ALLOWED_HOSTS=54.242.248.245
DJANGO_SECRET_KEY=your-secret-key
```

### **Frontend example (`nms/frontend/.env.prod.fe`)**

```env
REACT_APP_API_URL=http://54.242.248.245/api
REACT_APP_FRONTEND_URL=http://54.242.248.245
```

---

## 4️⃣ Build & Run Production Containers

Use the **`build.sh` script**. Make sure it’s executable:

```bash
chmod +x build.sh
```

Run production:

```bash
./build.sh prod
```

> This will build React, collect Django static files, and start all Docker containers including Nginx, backend, frontend, and Redis.

Check logs:

```bash
docker-compose logs -f
```

---

## 5️⃣ Access the App

* **Frontend (React SPA):** `http://54.242.248.245/`
* **Backend Admin:** `http://54.242.248.245/admin/login/?next=/admin/`
