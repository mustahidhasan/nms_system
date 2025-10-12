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

## 3️⃣ Configure `.env` Files

You have **two environment files**:

* **`.env.dev`** → for local development
* **`.env.prod`** → for production

### **.env.prod (example)**

```env
# Host & ports
HOST_URL=http://50.17.3.155
FRONTEND_PORT=80
BACKEND_PORT=8000
DEBUG=False
ALLOWED_HOSTS=50.17.3.155
```

> For local development, use `.env.dev`:

```env
HOST_URL=http://localhost
FRONTEND_PORT=3000
BACKEND_PORT=8000
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 4️⃣ Build & Run Containers Using `build.sh`

You now use the **`build.sh` script** to build and start containers for dev or prod. This handles environment variables and static files automatically.

**make sure `build.sh` is executable:**
```bash
chmod +x build.sh
```
**Local Development:**

```bash
./build.sh dev
```

**Production (server, e.g., 50.17.3.155):**

```bash
./build.sh prod
```

Check logs:

```bash
docker-compose logs -f
```

---

## 5️⃣ Access the App

* **Frontend (React):**

  * Local: `http://localhost:3000`
  * Production: `http://50.17.3.155/`

* **Backend Admin:**

  * Local: `http://localhost:8000/admin/`
  * Production: `http://50.17.3.155:8000/admin/`
