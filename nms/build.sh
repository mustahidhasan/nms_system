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
DIAGNOSTICS_DIR="$SCRIPT_DIR"
ENV_ROOT_DIR="$SCRIPT_DIR/config/env"
BACKEND_ENV_DEV_FILE="$ENV_ROOT_DIR/backend/.env.dev"
BACKEND_ENV_PROD_FILE="$ENV_ROOT_DIR/backend/.env.prod"
BACKEND_ENV_DEV_EXAMPLE="$ENV_ROOT_DIR/backend/.env.dev.example"
BACKEND_ENV_PROD_EXAMPLE="$ENV_ROOT_DIR/backend/.env.prod.example"
FRONTEND_APP_ENV_DEV_FILE="$ENV_ROOT_DIR/frontend/.env.dev"
FRONTEND_APP_ENV_PROD_FILE="$ENV_ROOT_DIR/frontend/.env.prod"
FRONTEND_APP_ENV_DEV_EXAMPLE="$ENV_ROOT_DIR/frontend/.env.dev.example"
FRONTEND_APP_ENV_PROD_EXAMPLE="$ENV_ROOT_DIR/frontend/.env.prod.example"
FRONTEND_WORKER_ENV_DEV_FILE="$ENV_ROOT_DIR/frontend/.env.worker.dev"
FRONTEND_WORKER_ENV_PROD_FILE="$ENV_ROOT_DIR/frontend/.env.worker.prod"
FRONTEND_WORKER_ENV_DEV_EXAMPLE="$ENV_ROOT_DIR/frontend/.env.worker.dev.example"
FRONTEND_WORKER_ENV_PROD_EXAMPLE="$ENV_ROOT_DIR/frontend/.env.worker.prod.example"
DIAGNOSTICS_ENV_DEV_FILE="$ENV_ROOT_DIR/diagnostics/.env.dev"
DIAGNOSTICS_ENV_PROD_FILE="$ENV_ROOT_DIR/diagnostics/.env.prod"
DIAGNOSTICS_ENV_DEV_EXAMPLE="$ENV_ROOT_DIR/diagnostics/.env.dev.example"
DIAGNOSTICS_ENV_PROD_EXAMPLE="$ENV_ROOT_DIR/diagnostics/.env.prod.example"
LOCAL_DB_PERSIST_DIR="$SCRIPT_DIR/db.dev"
BACKEND_PORT="${BACKEND_PORT:-8787}"
FRONTEND_PORT="${FRONTEND_PORT:-8788}"
BACKEND_INSPECTOR_PORT="${BACKEND_INSPECTOR_PORT:-9230}"
FRONTEND_INSPECTOR_PORT="${FRONTEND_INSPECTOR_PORT:-9231}"
DIAGNOSTICS_PORT="${DIAGNOSTICS_PORT:-8000}"
DIAGNOSTICS_HOST="${DIAGNOSTICS_HOST:-127.0.0.1}"
DIAGNOSTICS_EXECUTOR_TOKEN="${DIAGNOSTICS_EXECUTOR_TOKEN:-replace-with-shared-executor-token}"
SQLITE_DB_PATH="${SQLITE_DB_PATH:-$SCRIPT_DIR/db.dev.sqlite3}"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python}"
CF_ENV="${CLOUDFLARE_ENV:-prod}"

ensure_env_file() {
  local target="$1"
  local fallback_example="$2"
  if [[ -f "$target" ]]; then
    return 0
  fi
  if [[ -f "$fallback_example" ]]; then
    cp "$fallback_example" "$target"
    echo "[env] Created $target from example template."
    return 0
  fi
  echo "[env] Missing env file: $target"
  return 1
}

sync_runtime_env_files() {
  local env_name="$1"
  if [[ "$env_name" == "dev" ]]; then
    ensure_env_file "$BACKEND_ENV_DEV_FILE" "$BACKEND_ENV_DEV_EXAMPLE"
    ensure_env_file "$FRONTEND_APP_ENV_DEV_FILE" "$FRONTEND_APP_ENV_DEV_EXAMPLE"
    ensure_env_file "$FRONTEND_WORKER_ENV_DEV_FILE" "$FRONTEND_WORKER_ENV_DEV_EXAMPLE"
    ensure_env_file "$DIAGNOSTICS_ENV_DEV_FILE" "$DIAGNOSTICS_ENV_DEV_EXAMPLE"

    cp "$BACKEND_ENV_DEV_FILE" "$BACKEND_DIR/.env.dev"
    cp "$FRONTEND_APP_ENV_DEV_FILE" "$FRONTEND_APP_DIR/.env.dev"
    cp "$FRONTEND_WORKER_ENV_DEV_FILE" "$FRONTEND_WORKER_DIR/.env.dev"
  else
    ensure_env_file "$BACKEND_ENV_PROD_FILE" "$BACKEND_ENV_PROD_EXAMPLE"
    ensure_env_file "$FRONTEND_APP_ENV_PROD_FILE" "$FRONTEND_APP_ENV_PROD_EXAMPLE"
    ensure_env_file "$FRONTEND_WORKER_ENV_PROD_FILE" "$FRONTEND_WORKER_ENV_PROD_EXAMPLE"
    ensure_env_file "$DIAGNOSTICS_ENV_PROD_FILE" "$DIAGNOSTICS_ENV_PROD_EXAMPLE"

    cp "$BACKEND_ENV_PROD_FILE" "$BACKEND_DIR/.env.prod"
    cp "$FRONTEND_APP_ENV_PROD_FILE" "$FRONTEND_APP_DIR/.env.prod"
    cp "$FRONTEND_WORKER_ENV_PROD_FILE" "$FRONTEND_WORKER_DIR/.env.prod"
  fi
}

ensure_node_modules() {
  if [[ ! -d "$1/node_modules" ]]; then
    (cd "$1" && npm install)
  fi
}

prepare_frontend_env() {
  local env_name="$1"
  if [[ "$env_name" == "dev" ]]; then
    cp "$FRONTEND_APP_ENV_DEV_FILE" "$FRONTEND_APP_DIR/.env.local"
  else
    cp "$FRONTEND_APP_ENV_PROD_FILE" "$FRONTEND_APP_DIR/.env.production.local"
  fi
}

run_dev() {
  sync_runtime_env_files dev

  if [[ -f "$DIAGNOSTICS_ENV_DEV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$DIAGNOSTICS_ENV_DEV_FILE"
    set +a
  fi

  mkdir -p "$LOCAL_DB_PERSIST_DIR"

  ensure_node_modules "$BACKEND_DIR"
  ensure_node_modules "$FRONTEND_WORKER_DIR"
  ensure_node_modules "$FRONTEND_APP_DIR"

  prepare_frontend_env dev

  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "[dev] Creating local Python virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
  fi

  echo "[dev] Ensuring Django diagnostics service dependencies in virtualenv..."
  if ! "$PYTHON_BIN" -c "import django" >/dev/null 2>&1; then
    "$PYTHON_BIN" -m pip install --upgrade pip >/dev/null 2>&1 || true
    (cd "$DIAGNOSTICS_DIR" && "$PYTHON_BIN" -m pip install -r requirements.txt)
  fi

  echo "[dev] Running Django migrations for diagnostics service..."
  (
    cd "$DIAGNOSTICS_DIR"
    export SQLITE_DB_PATH="$SQLITE_DB_PATH"
    export DEBUG=True
    export DIAGNOSTICS_EXECUTOR_TOKEN="$DIAGNOSTICS_EXECUTOR_TOKEN"
    "$PYTHON_BIN" manage.py migrate --noinput > /tmp/nms_diagnostics_migrate.log 2>&1
  )

  echo "[dev] Starting diagnostics service on http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}"
  (
    cd "$DIAGNOSTICS_DIR"
    export SQLITE_DB_PATH="$SQLITE_DB_PATH"
    export DEBUG=True
    export DIAGNOSTICS_EXECUTOR_TOKEN="$DIAGNOSTICS_EXECUTOR_TOKEN"
    "$PYTHON_BIN" manage.py runserver "${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}" > /tmp/nms_diagnostics_service.log 2>&1
  ) &
  DIAGNOSTICS_PID=$!

  for _ in {1..30}; do
    if curl -sS "http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}/" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

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
    DIAGNOSTICS_EXECUTOR_URL="http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}" \
      DIAGNOSTICS_EXECUTOR_TOKEN="$DIAGNOSTICS_EXECUTOR_TOKEN" \
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
    kill "$DIAGNOSTICS_PID" "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$DIAGNOSTICS_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  }
  trap cleanup EXIT INT TERM

  echo "[dev] Workers running:"
  echo "      backend  -> http://127.0.0.1:${BACKEND_PORT}"
  echo "      frontend -> http://127.0.0.1:${FRONTEND_PORT}"
  echo "      diagnostics -> http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}"
  echo "      diagnostics log: /tmp/nms_diagnostics_service.log"
  echo "      backend log:  /tmp/nms_backend_worker.log"
  echo "      frontend log: /tmp/nms_frontend_worker.log"

  wait "$DIAGNOSTICS_PID" "$BACKEND_PID" "$FRONTEND_PID"
}

run_prod() {
  sync_runtime_env_files prod

  if [[ -f "$DIAGNOSTICS_ENV_PROD_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$DIAGNOSTICS_ENV_PROD_FILE"
    set +a
  fi

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

  echo "[prod] Diagnostics service deployment:"
  if [[ -x "$SCRIPT_DIR/scripts/deploy_diagnostics_service.sh" ]]; then
    DIAGNOSTICS_EXECUTOR_TOKEN="$DIAGNOSTICS_EXECUTOR_TOKEN" "$SCRIPT_DIR/scripts/deploy_diagnostics_service.sh" "$CF_ENV"
  else
    echo "  scripts/deploy_diagnostics_service.sh not found. Deploy diagnostics service separately."
  fi

  echo "[prod] Deployment complete."
}

if [[ "$MODE" == "dev" ]]; then
  run_dev
else
  run_prod
fi
