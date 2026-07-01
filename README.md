# Masareef

Masareef is a local-first CLI expense tracker for people who budget in USD and spend in EGP.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
masareef db init
masareef sync-fx
masareef budget set 800
masareef add 450 food "dinner"
masareef status
```

The database lives in `~/.masareef/masareef.db` by default. Set `MASAREEF_HOME` to use a different directory.

## Commands

```bash
masareef db init
masareef sync-fx
masareef sync-fx --backfill
masareef categories list
masareef categories add cafes
masareef add 450 food "dinner" --date 2026-06-30
masareef edit 1 --amount 500 --note "updated"
masareef delete 1 --yes
masareef fix-rate 1
masareef list --month 2026-06
masareef budget set 800
masareef budget show
masareef status
masareef alert-check
masareef export csv --output expenses.csv
masareef import csv expenses.csv
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest
python -m build
```

The test suite enforces at least 70% coverage.
