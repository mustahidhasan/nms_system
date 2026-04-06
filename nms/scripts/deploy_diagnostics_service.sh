#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_NAME="${1:-prod}"

# This script intentionally delegates deployment to a concrete command configured
# by environment, so teams can use Cloudflare Containers, another Cloudflare
# compute target, or an external CI pipeline while keeping build.sh stable.
DEPLOY_CMD="${DIAGNOSTICS_DEPLOY_CMD:-}"
if [[ -z "$DEPLOY_CMD" ]]; then
  echo "[diagnostics] DIAGNOSTICS_DEPLOY_CMD is not set."
  echo "[diagnostics] Example:"
  echo "  export DIAGNOSTICS_DEPLOY_CMD='cd $ROOT_DIR/diagnostics && npx wrangler containers deploy --env ${ENV_NAME}'"
  exit 0
fi

echo "[diagnostics] Running deployment command for env '${ENV_NAME}'..."
/bin/sh -lc "$DEPLOY_CMD"
