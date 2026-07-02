$ErrorActionPreference = "Stop"

$demoHome = Join-Path $PSScriptRoot "..\.demo-masareef"
if (Test-Path $demoHome) {
    Remove-Item -Recurse -Force $demoHome
}
New-Item -ItemType Directory -Force $demoHome | Out-Null
$env:MASAREEF_HOME = (Resolve-Path $demoHome).Path

Write-Host "`n$ masareef db init" -ForegroundColor Cyan
python -m masareef.cli db init

Write-Host "`n$ masareef categories list" -ForegroundColor Cyan
python -m masareef.cli categories list

Write-Host "`n$ python - <<seed a fixed demo FX rate>>" -ForegroundColor Cyan
python -c "from datetime import date; from decimal import Decimal; from masareef.db import init_db, session_scope; from masareef.services.fx import store_rate; init_db(); session = session_scope().__enter__(); store_rate(session, date(2026, 6, 30), Decimal('50'), 'demo'); session.close()"

Write-Host "`n$ masareef budget set 800 --month 2026-06" -ForegroundColor Cyan
python -m masareef.cli budget set 800 --month 2026-06

Write-Host "`n$ masareef add 450 food `"dinner with friends`" --date 2026-06-30" -ForegroundColor Cyan
python -m masareef.cli add 450 food "dinner with friends" --date 2026-06-30

Write-Host "`n$ masareef add 85 transport `"ride home`" --date 2026-06-30" -ForegroundColor Cyan
python -m masareef.cli add 85 transport "ride home" --date 2026-06-30

Write-Host "`n$ masareef list --month 2026-06" -ForegroundColor Cyan
python -m masareef.cli list --month 2026-06

Write-Host "`n$ masareef status --date 2026-06-30" -ForegroundColor Cyan
python -m masareef.cli status --date 2026-06-30

Write-Host "`n$ masareef export csv --output demo-expenses.csv" -ForegroundColor Cyan
python -m masareef.cli export csv --output (Join-Path $demoHome "demo-expenses.csv")

Write-Host "`nDemo data stored in $demoHome" -ForegroundColor Green
