# NMS Project - Production Deployment

This guide explains how to deploy the NMS project to an AWS EC2 instance for production.

---

## 1. Upload the project to the server

Use `scp` to copy your project folder to the EC2 instance:

```bash
scp -i your-key.pem -r /path/to/your/project ec2-user@EC2_PUBLIC_IP:~/nms
````

* Replace `your-key.pem` with your private key file.
* Replace `/path/to/your/project` with the local path to your NMS project.
* Replace `EC2_PUBLIC_IP` with the public IP of your EC2 instance.

---

## 2. Connect to the EC2 instance

```bash
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
cd ~/
unzip nms.zip
cd nms
```

---

## 3. Install Docker and Docker Compose

```bash
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
exit
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 4. Update the `.env` file

Inside your project folder on the server, set the production environment variables:

```
ALLOWED_HOSTS=EC2_PUBLIC_IP
DEBUG=False
SECRET_KEY=<YOUR_SECRET_KEY>
```

* Replace `<YOUR_SECRET_KEY>` with a secure secret key.
* Replace `EC2_PUBLIC_IP` with your server's public IP.

---

## 5. Build and start Docker containers

```bash
cd ~/nms
docker-compose build --no-cache
docker-compose up -d
```

* The application will now run in the background.
* Logs can be viewed with:

```bash
docker-compose logs -f
```

---

## 6. Security Groups

Ensure your EC2 instance security group allows:

* Port 80 (HTTP)
* Port 443 (HTTPS) if using SSL
* Port 8000 (optional, for direct Django access)

