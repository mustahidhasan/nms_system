#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-prod}"
if [[ "$MODE" != "prod" ]]; then
  echo "Usage: ./deploy.sh prod"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

bootstrap_env_prod() {
  local env_root="$ROOT_DIR/nms/config/env"
  local fe_dir="$env_root/frontend"
  local diag_dir="$env_root/diagnostics"

  [[ -f "$fe_dir/.env.prod" ]] || cp "$fe_dir/.env.prod.example" "$fe_dir/.env.prod"
  [[ -f "$fe_dir/.env.worker.prod" ]] || cp "$fe_dir/.env.worker.prod.example" "$fe_dir/.env.worker.prod"
  [[ -f "$diag_dir/.env.prod" ]] || cp "$diag_dir/.env.prod.example" "$diag_dir/.env.prod"
}

bootstrap_env_prod
exec bash "$ROOT_DIR/nms/run.sh" prod
