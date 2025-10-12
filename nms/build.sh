#!/bin/bash

# Usage: ./build.sh dev OR ./build.sh prod

ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
  echo "Building Production Environment..."
  BACKEND_ENV_FILE=".env.prod.be"
  FRONTEND_ENV_FILE=".env.prod.fe"
  COMPOSE_FILE="docker-compose.prod.yml"
else
  echo "Building Development Environment..."
  BACKEND_ENV_FILE=".env.dev.be"
  FRONTEND_ENV_FILE=".env.dev.fe"
  COMPOSE_FILE="docker-compose.dev.yml"
fi

export BACKEND_ENV_FILE
export FRONTEND_ENV_FILE

echo "Building containers with BACKEND_ENV_FILE=$BACKEND_ENV_FILE and FRONTEND_ENV_FILE=$FRONTEND_ENV_FILE..."

# Build frontend with build-arg for env
docker-compose -f $COMPOSE_FILE build --build-arg ENV_FILE=$FRONTEND_ENV_FILE

# Start all containers
docker-compose -f $COMPOSE_FILE up -d

echo "$ENV environment is up!"
