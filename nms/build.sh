#!/bin/bash
# Usage: ./build.sh dev OR ./build.sh prod

ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
  echo "Building Production Environment..."
  ENV_FILE_BE=".env.prod.be"
  ENV_FILE_FE=".env.prod.fe"
  HOST_IP="3.90.164.200"
  COMPOSE_FILE="docker-compose.prod.yml"

  # Generate self-signed SSL certs if they don't exist
  CERT_DIR="./certs"
  mkdir -p $CERT_DIR
  if [ ! -f "$CERT_DIR/selfsigned.crt" ] || [ ! -f "$CERT_DIR/selfsigned.key" ]; then
    echo "Generating self-signed SSL certificate..."
    sudo openssl req -x509 -nodes -days 365 \
      -newkey rsa:2048 \
      -keyout "$CERT_DIR/selfsigned.key" \
      -out "$CERT_DIR/selfsigned.crt" \
      -subj "/CN=$HOST_IP"
  else
    echo "SSL certificates already exist. Skipping generation."
  fi
else
  echo "Building Development Environment..."
  ENV_FILE_BE=".env.dev.be"
  ENV_FILE_FE=".env.dev.fe"
  HOST_IP="localhost"
  COMPOSE_FILE="docker-compose.dev.yml"
fi

export HOST_IP

echo "Building backend container with $ENV_FILE_BE..."
docker-compose -f $COMPOSE_FILE build backend \
  --build-arg ENV_FILE=$ENV_FILE_BE

echo "Building frontend container with $ENV_FILE_FE..."
docker-compose -f $COMPOSE_FILE build frontend \
  --build-arg ENV_FILE=$ENV_FILE_FE

echo "Starting all containers..."
docker-compose -f $COMPOSE_FILE up -d

echo "$ENV environment is up!"
