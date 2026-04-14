#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

COMPOSE_BIN=(docker-compose)
if ! command -v "${COMPOSE_BIN[0]}" >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_BIN=(docker compose)
  else
    echo "Neither docker-compose nor docker compose is available. Please install Docker Compose."
    exit 1
  fi
fi

"${COMPOSE_BIN[@]}" -f docker-compose.prod.yml down

