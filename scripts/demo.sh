#!/usr/bin/env bash
set -euo pipefail

DEMO_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.demo-masareef"
rm -rf "$DEMO_HOME"
mkdir -p "$DEMO_HOME"
export MASAREEF_HOME="$DEMO_HOME"

run() {
  printf "\n$ %s\n" "$*"
  "$@"
}

run python -m masareef.cli db init
run python -m masareef.cli categories list

printf "\n$ python - <<seed a fixed demo FX rate>>\n"
python - <<'PY'
from datetime import date
from decimal import Decimal

from masareef.db import init_db, session_scope
from masareef.services.fx import store_rate

init_db()
with session_scope() as session:
    store_rate(session, date(2026, 6, 30), Decimal("50"), "demo")
PY

run python -m masareef.cli budget set 800 --month 2026-06
run python -m masareef.cli add 450 food "dinner with friends" --date 2026-06-30
run python -m masareef.cli add 85 transport "ride home" --date 2026-06-30
run python -m masareef.cli list --month 2026-06
run python -m masareef.cli status --date 2026-06-30
run python -m masareef.cli export csv --output "$DEMO_HOME/demo-expenses.csv"

printf "\nDemo data stored in %s\n" "$DEMO_HOME"
