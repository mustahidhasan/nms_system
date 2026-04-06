#!/usr/bin/env bash
# Primary entrypoint:
#   ./build.sh dev   -> run backend + frontend Workers locally on separate ports
#   ./build.sh prod  -> migrate D1 and deploy backend + frontend Workers

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-dev}"
if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
  echo "Invalid mode '$MODE'. Use: ./build.sh dev OR ./build.sh prod"
  exit 1
fi

BACKEND_DIR="$SCRIPT_DIR/workers/backend"
FRONTEND_WORKER_DIR="$SCRIPT_DIR/workers/frontend"
FRONTEND_APP_DIR="$SCRIPT_DIR/frontend"
LOCAL_DB_PERSIST_DIR="$SCRIPT_DIR/db.dev"
BACKEND_PORT="${BACKEND_PORT:-8787}"
FRONTEND_PORT="${FRONTEND_PORT:-8788}"
BACKEND_INSPECTOR_PORT="${BACKEND_INSPECTOR_PORT:-9230}"
FRONTEND_INSPECTOR_PORT="${FRONTEND_INSPECTOR_PORT:-9231}"
CF_ENV="${CLOUDFLARE_ENV:-prod}"

ensure_node_modules() {
  if [[ ! -d "$1/node_modules" ]]; then
    (cd "$1" && npm install)
  fi
}

prepare_frontend_env() {
  local env_name="$1"
  if [[ "$env_name" == "dev" ]]; then
    cp "$FRONTEND_APP_DIR/.env.dev" "$FRONTEND_APP_DIR/.env.local"
  else
    cp "$FRONTEND_APP_DIR/.env.prod" "$FRONTEND_APP_DIR/.env.production.local"
  fi
}

run_dev() {
  mkdir -p "$LOCAL_DB_PERSIST_DIR"

  ensure_node_modules "$BACKEND_DIR"
  ensure_node_modules "$FRONTEND_WORKER_DIR"
  ensure_node_modules "$FRONTEND_APP_DIR"

  prepare_frontend_env dev

  echo "[dev] Building frontend assets for frontend Worker..."
  (cd "$FRONTEND_APP_DIR" && npm run build)

  echo "[dev] Applying local D1 schema (persisted under db.dev)..."
  (
    cd "$BACKEND_DIR"
    npx wrangler d1 execute NMS_DB --local --file=./schema.sql --persist-to "$LOCAL_DB_PERSIST_DIR"
  )

  echo "[dev] Starting backend Worker on http://127.0.0.1:${BACKEND_PORT}"
  (
    cd "$BACKEND_DIR"
    npx wrangler dev --env dev --port "$BACKEND_PORT" --inspector-port "$BACKEND_INSPECTOR_PORT" --persist-to "$LOCAL_DB_PERSIST_DIR" > /tmp/nms_backend_worker.log 2>&1
  ) &
  BACKEND_PID=$!

  echo "[dev] Starting frontend Worker on http://127.0.0.1:${FRONTEND_PORT}"
  (
    cd "$FRONTEND_WORKER_DIR"
    npx wrangler dev --env dev --port "$FRONTEND_PORT" --inspector-port "$FRONTEND_INSPECTOR_PORT" > /tmp/nms_frontend_worker.log 2>&1
  ) &
  FRONTEND_PID=$!

  cleanup() {
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  }
  trap cleanup EXIT INT TERM

  echo "[dev] Workers running:"
  echo "      backend  -> http://127.0.0.1:${BACKEND_PORT}"
  echo "      frontend -> http://127.0.0.1:${FRONTEND_PORT}"
  echo "      backend log:  /tmp/nms_backend_worker.log"
  echo "      frontend log: /tmp/nms_frontend_worker.log"

  wait "$BACKEND_PID" "$FRONTEND_PID"
}

run_prod() {
  ensure_node_modules "$BACKEND_DIR"
  ensure_node_modules "$FRONTEND_WORKER_DIR"
  ensure_node_modules "$FRONTEND_APP_DIR"

  prepare_frontend_env prod

  echo "[prod] Building frontend assets..."
  (cd "$FRONTEND_APP_DIR" && npm run build)

  echo "[prod] Migrating D1 schema for env '$CF_ENV'..."
  (cd "$BACKEND_DIR" && npm run "d1:migrate:remote:${CF_ENV}")

  echo "[prod] Deploying backend Worker..."
  (cd "$BACKEND_DIR" && npm run "deploy:${CF_ENV}")

  echo "[prod] Deploying frontend Worker..."
  (cd "$FRONTEND_WORKER_DIR" && npm run "deploy:${CF_ENV}")

  echo "[prod] Deployment complete."
}

if [[ "$MODE" == "dev" ]]; then
  run_dev
else
  run_prod
fi
