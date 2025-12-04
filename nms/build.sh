#!/bin/bash
# Usage: ./build.sh dev OR ./build.sh prod

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_BIN=(docker-compose)
if ! command -v "${COMPOSE_BIN[0]}" >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_BIN=(docker compose)
  else
    echo "Neither docker-compose nor docker compose is available. Please install Docker Compose."
    exit 1
  fi
fi

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

for required_file in "$ENV_FILE_BE" "./frontend/$ENV_FILE_FE" "$COMPOSE_FILE"; do
  if [ ! -f "$required_file" ]; then
    echo "Required file '$required_file' not found."
    exit 1
  fi
done

export HOST_IP

echo "Building backend container with $ENV_FILE_BE..."
"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" build backend \
  --build-arg ENV_FILE="$ENV_FILE_BE"

echo "Building frontend container with $ENV_FILE_FE..."
"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" build frontend \
  --build-arg ENV_FILE="$ENV_FILE_FE"

# Apply database migrations before starting the stack to keep the schema up to date.
echo "Applying database migrations..."
"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" run --rm backend python manage.py migrate --noinput

echo "Starting all containers..."
"${COMPOSE_BIN[@]}" -f "$COMPOSE_FILE" up -d

echo "$ENV environment is up!"
