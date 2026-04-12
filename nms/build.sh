#!/usr/bin/env bash
# Backwards-compatible shim. Use ./run.sh instead.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/run.sh" "$@"
