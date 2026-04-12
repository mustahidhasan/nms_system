#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

XDG_ROOT_DIR="${XDG_ROOT_DIR:-$ROOT_DIR/nms/.xdg}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$XDG_ROOT_DIR/config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$XDG_ROOT_DIR/cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$XDG_ROOT_DIR/data}"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"

CMD="${1:-prod}"
case "$CMD" in
  login)
    (cd "$ROOT_DIR/nms/workers/frontend" && npx wrangler login)
    exit 0
    ;;
  logout)
    (cd "$ROOT_DIR/nms/workers/frontend" && npx wrangler logout)
    exit 0
    ;;
  token)
    # Sets a Cloudflare secret for the production environment without printing the token.
    # Override generation by providing DIAGNOSTICS_EXECUTOR_TOKEN in your env.
    TOKEN="${DIAGNOSTICS_EXECUTOR_TOKEN:-}"
    if [[ -z "$TOKEN" ]]; then
      TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    fi
    set +e
    printf '%s' "$TOKEN" | (cd "$ROOT_DIR/nms/workers/frontend" && npx wrangler secret put DIAGNOSTICS_EXECUTOR_TOKEN --env prod)
    STATUS=$?
    set -e
    if [[ $STATUS -ne 0 ]]; then
      echo "[prod] Failed to set secret DIAGNOSTICS_EXECUTOR_TOKEN."
      echo "[prod] If you previously deployed with DIAGNOSTICS_EXECUTOR_TOKEN as a plain env var, redeploy first to remove it:"
      echo "       bash deploy.sh prod"
      exit $STATUS
    fi
    echo "[prod] Set secret DIAGNOSTICS_EXECUTOR_TOKEN for env.prod"
    exit 0
    ;;
  prod) ;;
  *)
    echo "Usage: bash deploy.sh prod|login|logout|token"
    exit 1
    ;;
esac

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
