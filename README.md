# uploadthe project to server
```
ssh -i your-key.pem ec2-user@EC2_PUBLIC_IP
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
```
# steps to run this project 
- Update the .env file in nms folder with your own values
- Run the following commands in the terminal
```
docker-compose build --no-cache
docker-compose up
```