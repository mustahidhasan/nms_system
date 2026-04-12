#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

MODE="${1:-dev}"
if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
  echo "Usage: bash run.sh dev|prod"
  exit 1
fi

bootstrap_env() {
  local env_root="$ROOT_DIR/nms/config/env"
  local fe_dir="$env_root/frontend"
  local diag_dir="$env_root/diagnostics"
  local suffix="$1"

  local fe_app="$fe_dir/.env.${suffix}"
  local fe_app_ex="$fe_dir/.env.${suffix}.example"
  local fe_worker="$fe_dir/.env.worker.${suffix}"
  local fe_worker_ex="$fe_dir/.env.worker.${suffix}.example"
  local diag="$diag_dir/.env.${suffix}"
  local diag_ex="$diag_dir/.env.${suffix}.example"

  [[ -f "$fe_app" ]] || cp "$fe_app_ex" "$fe_app"
  [[ -f "$fe_worker" ]] || cp "$fe_worker_ex" "$fe_worker"
  [[ -f "$diag" ]] || cp "$diag_ex" "$diag"
}

if [[ "$MODE" == "dev" ]]; then
  bootstrap_env dev
else
  bootstrap_env prod
fi

exec bash "$ROOT_DIR/nms/run.sh" "$@"
