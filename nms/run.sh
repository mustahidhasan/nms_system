#!/usr/bin/env bash
# Primary entrypoint:
#   ./run.sh dev   -> run frontend Worker + diagnostics service locally
#   ./run.sh prod  -> migrate D1 and deploy frontend Worker (and diagnostics hook)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-dev}"
if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
  echo "Invalid mode '$MODE'. Use: ./run.sh dev OR ./run.sh prod"
  exit 1
fi

FRONTEND_WORKER_DIR="$SCRIPT_DIR/workers/frontend"
FRONTEND_APP_DIR="$SCRIPT_DIR/frontend"
DIAGNOSTICS_DIR="$SCRIPT_DIR"
ENV_ROOT_DIR="$SCRIPT_DIR/config/env"
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
LOCAL_DB_PERSIST_DIR="$SCRIPT_DIR/dev.db"
FRONTEND_PORT="${FRONTEND_PORT:-8788}"
FRONTEND_IP="${FRONTEND_IP:-127.0.0.1}"
FRONTEND_INSPECTOR_PORT="${FRONTEND_INSPECTOR_PORT:-9231}"
FRONTEND_INSPECTOR_IP="${FRONTEND_INSPECTOR_IP:-127.0.0.1}"
DIAGNOSTICS_PORT="${DIAGNOSTICS_PORT:-8000}"
DIAGNOSTICS_HOST="${DIAGNOSTICS_HOST:-127.0.0.1}"
DIAGNOSTICS_EXECUTOR_TOKEN="${DIAGNOSTICS_EXECUTOR_TOKEN:-replace-with-shared-executor-token}"
SQLITE_DB_PATH="${SQLITE_DB_PATH:-$SCRIPT_DIR/db.dev.sqlite3}"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python}"
CF_ENV="${CLOUDFLARE_ENV:-prod}"

XDG_ROOT_DIR="${XDG_ROOT_DIR:-$SCRIPT_DIR/.xdg}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$XDG_ROOT_DIR/config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$XDG_ROOT_DIR/cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$XDG_ROOT_DIR/data}"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"

is_port_free() {
  local host="$1"
  local port="$2"
  python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind((host, port))
except OSError:
    sys.exit(1)
finally:
    s.close()
sys.exit(0)
PY
}

pick_free_port() {
  local host="$1"
  local base_port="$2"
  local span="${3:-20}"
  local port
  for ((port = base_port; port < base_port + span; port++)); do
    if is_port_free "$host" "$port"; then
      echo "$port"
      return 0
    fi
  done
  return 1
}

ensure_env_file() {
  local target="$1"
  local fallback_example="$2"
  local force="${NMS_ENV_FROM_EXAMPLES:-}"

  if [[ -z "$force" && -f "$target" ]]; then
    return 0
  fi

  if [[ -f "$fallback_example" ]]; then
    cp "$fallback_example" "$target"
    if [[ -n "$force" ]]; then
      echo "[env] Reset $target from example template (NMS_ENV_FROM_EXAMPLES=1)."
    else
      echo "[env] Created $target from example template."
    fi
    return 0
  fi

  echo "[env] Missing env example file: $fallback_example"
  return 1
}

sync_runtime_env_files() {
  local env_name="$1"
  if [[ "$env_name" == "dev" ]]; then
    ensure_env_file "$FRONTEND_APP_ENV_DEV_FILE" "$FRONTEND_APP_ENV_DEV_EXAMPLE"
    ensure_env_file "$FRONTEND_WORKER_ENV_DEV_FILE" "$FRONTEND_WORKER_ENV_DEV_EXAMPLE"
    ensure_env_file "$DIAGNOSTICS_ENV_DEV_FILE" "$DIAGNOSTICS_ENV_DEV_EXAMPLE"

    cp "$FRONTEND_APP_ENV_DEV_FILE" "$FRONTEND_APP_DIR/.env.dev"
    cp "$FRONTEND_WORKER_ENV_DEV_FILE" "$FRONTEND_WORKER_DIR/.env.dev"
  else
    ensure_env_file "$FRONTEND_APP_ENV_PROD_FILE" "$FRONTEND_APP_ENV_PROD_EXAMPLE"
    ensure_env_file "$FRONTEND_WORKER_ENV_PROD_FILE" "$FRONTEND_WORKER_ENV_PROD_EXAMPLE"
    ensure_env_file "$DIAGNOSTICS_ENV_PROD_FILE" "$DIAGNOSTICS_ENV_PROD_EXAMPLE"

    cp "$FRONTEND_APP_ENV_PROD_FILE" "$FRONTEND_APP_DIR/.env.prod"
    cp "$FRONTEND_WORKER_ENV_PROD_FILE" "$FRONTEND_WORKER_DIR/.env.prod"
  fi
}

ensure_node_modules() {
  if [[ ! -d "$1/node_modules" ]]; then
    (cd "$1" && npm install)
  fi
}

assert_wrangler_prod_ready() {
  local config_file="$FRONTEND_WORKER_DIR/wrangler.toml"
  if [[ ! -f "$config_file" ]]; then
    echo "[prod] Missing $config_file"
    exit 1
  fi

  if grep -q 'account_id = "REPLACE_WITH_CLOUDFLARE_ACCOUNT_ID"' "$config_file"; then
    echo "[prod] Set Cloudflare account_id in $config_file"
    exit 1
  fi

  local env_name="$CF_ENV"
  local prod_db_id
  local prod_preview_id
  prod_db_id="$(
    awk -v env="$env_name" '
      $0 ~ "^\\[\\[env\\." env "\\.d1_databases\\]\\]" { in_d1=1; next }
      in_d1 && $0 ~ "^\\[" { in_d1=0 }
      in_d1 && $0 ~ "^[[:space:]]*database_id[[:space:]]*=" {
        n = split($0, a, "\""); if (n >= 3) { print a[2]; exit }
      }
    ' "$config_file"
  )"
  prod_preview_id="$(
    awk -v env="$env_name" '
      $0 ~ "^\\[\\[env\\." env "\\.d1_databases\\]\\]" { in_d1=1; next }
      in_d1 && $0 ~ "^\\[" { in_d1=0 }
      in_d1 && $0 ~ "^[[:space:]]*preview_database_id[[:space:]]*=" {
        n = split($0, a, "\""); if (n >= 3) { print a[2]; exit }
      }
    ' "$config_file"
  )"

  if [[ -z "${prod_db_id:-}" || "$prod_db_id" == REPLACE_WITH_* ]]; then
    echo "[prod] Set D1 database_id in $config_file (env.${env_name})"
    exit 1
  fi

  if [[ -n "${prod_preview_id:-}" && "$prod_preview_id" == REPLACE_WITH_* ]]; then
    echo "[prod] Set D1 preview_database_id in $config_file (env.${env_name})"
    echo "[prod] Or remove preview_database_id if you don't use preview DB."
    exit 1
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

  if ! is_port_free "$DIAGNOSTICS_HOST" "$DIAGNOSTICS_PORT"; then
    if curl -sS "http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}/" >/dev/null 2>&1; then
      echo "[dev] Diagnostics already running on http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}"
      DIAGNOSTICS_PID=""
    else
      echo "[dev] Diagnostics port ${DIAGNOSTICS_PORT} is already in use."
      exit 1
    fi
  else
    echo "[dev] Starting diagnostics service on http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}"
    (
      cd "$DIAGNOSTICS_DIR"
      export SQLITE_DB_PATH="$SQLITE_DB_PATH"
      export DEBUG=True
      export DIAGNOSTICS_EXECUTOR_TOKEN="$DIAGNOSTICS_EXECUTOR_TOKEN"
      "$PYTHON_BIN" manage.py runserver "${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}" > /tmp/nms_diagnostics_service.log 2>&1
    ) &
    DIAGNOSTICS_PID=$!
  fi

  for _ in {1..30}; do
    if curl -sS "http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}/" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  echo "[dev] Building frontend assets for frontend Worker..."
  (cd "$FRONTEND_APP_DIR" && npm run build)

  echo "[dev] Applying local D1 schema (persisted under dev.db)..."
  (
    cd "$FRONTEND_WORKER_DIR"
    npx wrangler d1 execute NMS_DB --local --file=./schema.sql --persist-to "$LOCAL_DB_PERSIST_DIR"
  )

  local inspector_port
  inspector_port="$(pick_free_port "$FRONTEND_INSPECTOR_IP" "$FRONTEND_INSPECTOR_PORT" 40 || true)"
  if [[ -z "$inspector_port" ]]; then
    echo "[dev] Could not find a free inspector port starting at ${FRONTEND_INSPECTOR_PORT}."
    exit 1
  fi
  if [[ "$inspector_port" != "$FRONTEND_INSPECTOR_PORT" ]]; then
    echo "[dev] Frontend inspector port ${FRONTEND_INSPECTOR_PORT} in use; using ${inspector_port} instead."
  fi

  echo "[dev] Starting frontend Worker on http://${FRONTEND_IP}:${FRONTEND_PORT}"
  (
    cd "$FRONTEND_WORKER_DIR"
    npx wrangler dev --env dev --ip "$FRONTEND_IP" --port "$FRONTEND_PORT" --inspector-ip "$FRONTEND_INSPECTOR_IP" --inspector-port "$inspector_port" --persist-to "$LOCAL_DB_PERSIST_DIR" > /tmp/nms_frontend_worker.log 2>&1
  ) &
  FRONTEND_PID=$!

  for _ in {1..45}; do
    if curl -sS "http://localhost:${FRONTEND_PORT}/api" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  cleanup() {
    if [[ -n "${DIAGNOSTICS_PID:-}" ]]; then
      kill "$DIAGNOSTICS_PID" 2>/dev/null || true
      wait "$DIAGNOSTICS_PID" 2>/dev/null || true
    fi
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  }
  trap cleanup EXIT INT TERM

  echo "[dev] Services running:"
  echo "      frontend -> http://localhost:${FRONTEND_PORT}"
  echo "      frontend -> http://127.0.0.1:${FRONTEND_PORT}"
  if [[ "$FRONTEND_IP" != "127.0.0.1" && "$FRONTEND_IP" != "localhost" ]]; then
    echo "      frontend -> http://${FRONTEND_IP}:${FRONTEND_PORT}"
  fi
  echo "      diagnostics -> http://${DIAGNOSTICS_HOST}:${DIAGNOSTICS_PORT}"
  echo "      diagnostics log: /tmp/nms_diagnostics_service.log"
  echo "      frontend log: /tmp/nms_frontend_worker.log"

  wait "$DIAGNOSTICS_PID" "$FRONTEND_PID"
}

run_prod() {
  sync_runtime_env_files prod

  if [[ -f "$DIAGNOSTICS_ENV_PROD_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$DIAGNOSTICS_ENV_PROD_FILE"
    set +a
  fi

  ensure_node_modules "$FRONTEND_WORKER_DIR"
  ensure_node_modules "$FRONTEND_APP_DIR"

  prepare_frontend_env prod

  assert_wrangler_prod_ready

  echo "[prod] Building frontend assets..."
  (cd "$FRONTEND_APP_DIR" && npm run build)

  echo "[prod] Migrating D1 schema for env '$CF_ENV'..."
  (cd "$FRONTEND_WORKER_DIR" && npm run "d1:migrate:remote:${CF_ENV}")

  echo "[prod] Deploying frontend Worker..."
  (cd "$FRONTEND_WORKER_DIR" && npm run "deploy:${CF_ENV}")

  echo "[prod] Deployment complete."
}

if [[ "$MODE" == "dev" ]]; then
  run_dev
else
  run_prod
fi
