# Changelog

## v0.1.0 - 2026-07-02

Initial public release of Masareef.

### Added

- Local SQLite database with seeded spending categories.
- Expense add, list, edit, delete, and FX-rate repair commands.
- USD/EGP FX sync with primary and fallback providers.
- Historical FX-rate storage and stale-rate fallback for offline logging.
- USD monthly budgets with month-specific overrides.
- Current-month status dashboard with budget usage, projections, category totals, and overspend warnings.
- Cron-friendly `alert-check` command.
- Category management commands.
- CSV export and import.
- Deterministic demo scripts for Windows PowerShell and Bash.
- GitHub Actions CI for Python 3.10, 3.11, and 3.12.

### Quality

- Test suite covers service logic and CLI integration with isolated local databases.
- Coverage gate is set to 70%; current local coverage is above 80%.
- Package build verified with `python -m build`.
