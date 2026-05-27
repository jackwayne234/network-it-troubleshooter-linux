#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -x "$APP_DIR/.venv/bin/network-it-troubleshooter" ]; then
  echo "First-time setup is needed."
  "$APP_DIR/Setup_Prerequisites.sh"
fi
exec "$APP_DIR/.venv/bin/network-it-troubleshooter" "$@"
