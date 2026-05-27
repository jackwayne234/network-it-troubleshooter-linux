#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# Keep normal launches quiet. The Wayland text-input warning is a harmless Qt message.
export QT_LOGGING_RULES="qt.qpa.wayland.textinput.warning=false"
export PYTHONDONTWRITEBYTECODE=1

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

VENV_PYTHON="$APP_DIR/.venv/bin/python"
VENV_APP="$APP_DIR/.venv/bin/network-it-troubleshooter"

# Install dependencies only once for this local launcher.
# This avoids repeated pip cache warnings on every app open.
if [ ! -f .venv/.network-it-troubleshooter-installed ]; then
  PIP_NO_CACHE_DIR=1 "$VENV_PYTHON" -m pip install -e .
  touch .venv/.network-it-troubleshooter-installed
fi

if [ "${1:-}" = "--self-test" ]; then
  "$VENV_PYTHON" - <<'PY'
from network_it_troubleshooter.engine import analyze_report
from network_it_troubleshooter.work_package import steps_for_flow
analysis = analyze_report({"overall": {"status": "healthy"}, "results": []})
assert analysis.flow_used == "Healthy Flow"
assert steps_for_flow("Healthy Flow", "example.com")
print("SELF_TEST_PASS")
PY
  exit 0
fi

exec "$VENV_APP"
