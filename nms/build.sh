#!/bin/bash

# Usage: ./build.sh dev OR ./build.sh prod

ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
  echo "Building Production Environment..."
  ENV_FILE=".env.prod"
  HOST_IP="50.17.3.155"
  COMPOSE_FILE="docker-compose.prod.yml"
else
  echo "Building Development Environment..."
  ENV_FILE=".env.dev"
  HOST_IP="localhost"
  COMPOSE_FILE="docker-compose.dev.yml"
fi

# Export for use inside containers if needed
export ENV_FILE
export HOST_IP

echo "Building containers with ENV_FILE=$ENV_FILE..."

# Build with build-args
docker-compose -f $COMPOSE_FILE build \
  --build-arg ENV_FILE=$ENV_FILE

# Start the containers
docker-compose -f $COMPOSE_FILE up -d

echo "$ENV environment is up!"
