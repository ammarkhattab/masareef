# Masareef — Product Requirements Document & Implementation Plan

> **Masareef** (مصاريف, "expenses") — a Python CLI that lets Egyptian freelancers and professionals budget in USD while spending in EGP, with automatic FX syncing and budget alerts.

---

## Document metadata

| Field | Value |
|---|---|
| Document version | 1.0 |
| Status | Approved for build |
| Author | Ammar |
| Start date | Week 1, Monday |
| Target completion | End of Week 2 |
| Total effort | ~25–30 hours (2 weeks × ~15 hrs/week) |
| Learning tier | Beginner (project #1 in the 2-year roadmap) |

---

# Part 1 — Product Requirements Document (PRD)

## 1. Executive summary

Masareef is a single-user, local-first command-line expense tracker built specifically for Egyptians who earn in USD (freelancers, remote workers, expats returning home) but spend in EGP. It addresses the cognitive dissonance of FX volatility: someone can stay "on budget" in EGP while silently burning through their real USD-denominated savings. The tool logs expenses in EGP, pulls daily USD/EGP rates, and alerts the user when their monthly spending crosses a USD-anchored budget threshold — converting at the historical rate of each transaction, not a misleading "current" rate.

The product is intentionally scoped as a **CLI only, single-user, SQLite-backed** tool so the scope stays achievable inside two weeks for a complete beginner while still covering every foundational software engineering skill: Python packaging, CLI ergonomics, SQL modeling, HTTP clients, caching, testing, and Git discipline.

## 2. Problem statement & context

### 2.1 The problem

The Egyptian pound has lost roughly 70% of its value against the USD between 2022 and 2025, with several sharp devaluation events (March 2022, October 2022, January 2023, March 2024). An Egyptian freelancer earning $1,500/month experiences this as:

- In early 2022, $1,500 ≈ EGP 23,500
- By late 2024, $1,500 ≈ EGP 74,000
- A user whose rent "only went from EGP 5,000 to EGP 12,000" feels they're keeping up; in USD it went from $320 to $245 — they're actually *saving* money on rent.
- Conversely, a user whose "dinner out budget" grew from EGP 300 to EGP 800 over 3 years thinks they're overspending — but in USD, EGP 800 today ($16) is less than EGP 300 in 2022 ($19).

**The mental model fails in both directions.** Existing tools (Excel, YNAB, mobile apps) either require manual FX management or ignore the problem entirely.

### 2.2 Why a CLI, why now, why this scope

A CLI is appropriate because:
1. The target user is technical (freelance developer) and comfortable with terminals.
2. Daily logging through `masareef add 450 food "لحمة"` takes 3 seconds; opening an app takes 30.
3. It's the simplest scope that teaches real software engineering fundamentals end-to-end.
4. It can be cron-scheduled for automatic daily FX sync and alerts.

### 2.3 Why this matters for the builder (you)

This is project #1 in a 2-year AI engineer roadmap. Every downstream project reuses skills from here: SQLAlchemy models reappear in the FastAPI task API, HTTP clients reappear in every LLM wrapper, pytest discipline reappears everywhere, Git workflow compounds forever. **Ship this cleanly and the next 40 projects get easier.**

## 3. Goals, non-goals, success criteria

### 3.1 Goals (what this product must do)

| # | Goal | Priority |
|---|---|---|
| G1 | Log expenses in EGP quickly from the terminal | Must |
| G2 | Automatically fetch and store daily USD/EGP FX rates | Must |
| G3 | Let the user set a monthly budget anchored in USD | Must |
| G4 | Warn when EGP spending at historical rates crosses the USD budget | Must |
| G5 | Show current-month status in both currencies at a glance | Must |
| G6 | Categorize expenses and report by category | Must |
| G7 | Work offline (last cached FX rate) | Must |
| G8 | Export to CSV for backup and external analysis | Should |
| G9 | Import a month of transactions from CSV | Should |
| G10 | Be installable with a single `pipx install` command | Should |

### 3.2 Non-goals (explicitly excluded)

- No GUI, web UI, or mobile app. CLI only.
- No multi-user, no authentication, no cloud sync.
- No automatic bank statement scraping (v1).
- No investment tracking, net worth tracking, or income tracking beyond budget setting.
- No receipt OCR (that's project #53 in the roadmap).
- No forecasting or ML (that's project #46).
- No Arabic dialect parsing of natural-language expenses (Arabizi is out of scope for v1; it becomes project #66).

### 3.3 Success criteria

The project is considered successful if **all** of the following are true at the end of week 2:

1. **Functional:** All Must-priority goals (G1–G7) are implemented and tested.
2. **Quality:** Test coverage ≥ 70%, all tests pass in CI on every push.
3. **Usable:** You (the author) use it daily for at least one full week *before* writing the README.
4. **Portfolio:** GitHub repo is public with a polished README, a demo GIF, and a green CI badge.
5. **Distributed:** The tool is installable by others via `pipx install masareef` (from TestPyPI or PyPI) OR `pipx install git+https://github.com/<you>/masareef`.
6. **Written:** A 600–1000 word blog post explaining the problem and the build is published on your bilingual blog (project #11 will handle the blog; for now, a GitHub Gist or dev.to post works).

## 4. Target users & personas

### 4.1 Primary persona — "Ahmed the freelance developer"

| Attribute | Description |
|---|---|
| Age / Role | 24–32, freelance or remote software developer |
| Location | Cairo, Alexandria, or a Tier-2 Egyptian city |
| Income | $1,000–$5,000/month, paid via Payoneer/Wise |
| Spending | 100% in EGP (rent, groceries, delivery, rides) |
| Tech comfort | High — lives in terminal, uses Git daily |
| Key pain | Feels like he's "always broke" despite earning in USD; can't tell if inflation or overspending is to blame |
| Usage pattern | Logs expenses on his phone via SSH/Termux or on laptop each evening |

### 4.2 Secondary personas

- **Nour the consultant** — bills Gulf clients in USD, saves in EGP, wants to monitor real purchasing power.
- **You (the builder)** — use it as a daily tool, dogfood it to find the real bugs.

### 4.3 Anti-personas (people this tool is NOT for)

- Users uncomfortable with CLI. They should use a mobile app.
- Users who spend in multiple currencies. v1 is EGP-only spending, USD-only budgeting.
- Businesses with multi-user needs. This is strictly personal finance.

## 5. User stories & acceptance criteria

The following user stories define the MVP. Each has testable acceptance criteria.

### US-1: Log an expense quickly

> **As** a user, **I want** to log an expense with one command, **so that** I don't context-switch away from my terminal.

**Acceptance criteria:**
- `masareef add 450 food "بقاله"` stores the expense with amount=450 EGP, category=food, note="بقاله", date=today.
- If date is omitted, today's date (Africa/Cairo timezone) is used.
- If the FX rate for today exists in cache, the USD equivalent is stored; otherwise, the tool attempts a live fetch; if offline, it falls back to the most recent cached rate and warns the user.
- Invalid inputs (negative amounts, unknown categories) are rejected with a clear error message.
- The command returns within 200ms on cache hit.

### US-2: List recent expenses

> **As** a user, **I want** to see my recent expenses, **so that** I can verify what I logged.

**Acceptance criteria:**
- `masareef list` shows the last 20 expenses in a table with date, category, EGP amount, USD equivalent, and note.
- `masareef list --month 2026-04` filters to a specific month.
- `masareef list --category food` filters by category.
- Arabic text in the note column renders correctly (RTL alignment, no mojibake).

### US-3: Set a monthly budget in USD

> **As** a user, **I want** to set a budget in USD, **so that** my budget stays stable when the pound devalues.

**Acceptance criteria:**
- `masareef budget set 800` sets the monthly budget to $800 USD.
- `masareef budget show` displays the current budget plus the EGP-equivalent at today's rate.
- Budget persists across sessions.
- Budget can be overridden per month: `masareef budget set 1000 --month 2026-05`.

### US-4: Sync FX rates

> **As** a user, **I want** FX rates fetched automatically, **so that** my conversions are accurate.

**Acceptance criteria:**
- `masareef sync-fx` fetches today's USD/EGP rate from the primary API and stores it.
- If the primary API fails, the secondary API is tried. If both fail, the command exits with code 1 and a clear error message.
- `masareef sync-fx --backfill` fetches missing rates for the last 90 days.
- A successful sync is idempotent (rerunning on the same day doesn't duplicate).
- Rates are cached locally in SQLite.

### US-5: See current-month status

> **As** a user, **I want** a quick dashboard, **so that** I know where I stand without doing math.

**Acceptance criteria:**
- `masareef status` displays (for the current month):
  - Total spent in EGP and in USD (converted at each expense's historical rate).
  - Budget in USD and EGP (at today's rate).
  - Percentage of budget used.
  - Days remaining in the month.
  - Projected end-of-month spending based on daily average.
  - A warning if projected spending > budget.
- Output uses color: green (< 70%), yellow (70–90%), red (> 90%).

### US-6: Get budget alerts

> **As** a user, **I want** to be warned when I'm overspending, **so that** I can adjust before month-end.

**Acceptance criteria:**
- `masareef alert-check` exits with code 0 if under budget, code 2 if over, and prints a warning message.
- The command is cron-friendly (silent on green, noisy on red; `--quiet` flag suppresses even warnings except exit code).
- Thresholds are configurable (default: warn at 80%, alert at 100%).

### US-7: Manage categories

> **As** a user, **I want** to manage my spending categories, **so that** I can analyze my habits.

**Acceptance criteria:**
- `masareef categories list` shows all categories.
- `masareef categories add <name>` creates a category.
- `masareef categories rename <old> <new>` renames one.
- Default categories are seeded on first run: food, transport, rent, utilities, entertainment, health, shopping, other.

### US-8: Work offline

> **As** a user, **I want** the tool to work without internet, **so that** my logging isn't interrupted by ISP outages.

**Acceptance criteria:**
- All commands except `sync-fx` work fully offline using cached rates.
- When using a stale rate, the tool prints `⚠ Using FX rate from YYYY-MM-DD (N days old)` so the user knows.
- Offline-incurred expenses can be retroactively corrected via `masareef fix-rate <expense-id>` after the next sync.

### US-9 (Should): Export to CSV

> **As** a user, **I want** to export my data, **so that** I have a backup and can do ad-hoc analysis in Excel.

**Acceptance criteria:**
- `masareef export csv --output expenses.csv` writes all expenses.
- `masareef export csv --month 2026-04` writes one month.
- Output includes columns: id, date, category, amount_egp, amount_usd, fx_rate, note.

### US-10 (Should): Import from CSV

> **As** a user, **I want** to bulk-import expenses, **so that** I can backfill my history.

**Acceptance criteria:**
- `masareef import csv input.csv` loads rows matching the export schema.
- Invalid rows are reported but don't abort the import; a summary is printed at the end (X imported, Y skipped, Z reasons).

## 6. Functional requirements summary

| ID | Requirement | Priority |
|---|---|---|
| F-01 | CRUD for expenses (amount, category, date, note) | Must |
| F-02 | Default + user-defined categories | Must |
| F-03 | Automatic FX sync from primary + fallback API | Must |
| F-04 | Historical FX rate caching (per day) | Must |
| F-05 | USD-anchored monthly budget | Must |
| F-06 | Status dashboard with projection | Must |
| F-07 | Alert command suitable for cron | Must |
| F-08 | Graceful offline operation with stale-rate warnings | Must |
| F-09 | Arabic (UTF-8) support in notes | Must |
| F-10 | Beautiful terminal output (colors, tables) | Should |
| F-11 | CSV export and import | Should |
| F-12 | Configurable DB location via `MASAREEF_HOME` env var | Should |
| F-13 | `--dry-run` flag on mutating commands | Could |
| F-14 | Recurring expenses (rent, subscriptions) | Could (v2) |

## 7. Non-functional requirements

### 7.1 Performance

- Any command should complete in **< 500ms** on cache hit with <10k expenses.
- `sync-fx` with network should complete in **< 3s** on a healthy connection.
- Startup overhead (Python import time) should be **< 200ms**. (Lazy-import heavy deps like `requests` only inside commands that need them.)

### 7.2 Reliability

- No command should ever corrupt the database. Use SQLite transactions.
- External API failures must never crash the app; they degrade gracefully to cached data.
- Database file should be safe against concurrent runs (SQLite WAL mode).

### 7.3 Security & privacy

- All data stays local in `~/.masareef/masareef.db` (or `$MASAREEF_HOME`).
- No telemetry, no analytics, no phone-home.
- No secrets needed in v1 (the chosen FX APIs are keyless). If a keyed API is added later, keys go in `~/.masareef/.env`, never in the repo.

### 7.4 Portability

- Runs on Linux, macOS, Windows (WSL preferred on Windows).
- Python 3.10+ supported (match Ubuntu 22.04 LTS default).
- No native compiled dependencies in v1.

### 7.5 Usability

- `masareef --help` and `masareef <cmd> --help` must always work and be readable.
- Error messages must be actionable: "Category 'foody' not found. Did you mean 'food'? Run `masareef categories list` to see all." — not "KeyError: 'foody'".

### 7.6 Maintainability

- Each module < 300 lines.
- Type hints on every public function.
- Docstrings on every command.
- No function deeper than 3 levels of nesting.

## 8. Technical architecture

### 8.1 High-level architecture

```
┌──────────────────────────────────────────────────────────┐
│                        User Terminal                      │
└──────────────────────┬───────────────────────────────────┘
                       │ $ masareef add 450 food "قهوه"
                       ▼
┌──────────────────────────────────────────────────────────┐
│                 CLI Layer (Typer)                         │
│   Commands: add, list, status, budget, sync-fx, ...      │
└──────────────────────┬───────────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
┌─────────┐    ┌────────────────┐  ┌──────────────┐
│ Service │    │  FX Service     │  │  Reporting   │
│ Layer   │    │  (fetch + cache)│  │  (status, …) │
└────┬────┘    └────────┬───────┘  └──────┬───────┘
     │                  │                 │
     ▼                  ▼                 │
┌─────────────────────────────┐           │
│   Repository Layer           │◄──────────┘
│   (SQLAlchemy ORM)           │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐       ┌────────────────────┐
│   SQLite DB                  │       │  External APIs      │
│   ~/.masareef/masareef.db    │       │  open.er-api.com    │
└─────────────────────────────┘       │  frankfurter.app    │
                                       └────────────────────┘
```

### 8.2 Tech stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11 | Widely used, beginner-friendly, what the rest of the roadmap uses |
| CLI framework | Typer | Modern, type-hint driven, auto-generates `--help` |
| Terminal output | Rich | Beautiful tables, colors, RTL-safe rendering |
| Database | SQLite (via SQLAlchemy 2.0) | Zero-config; ORM patterns carry into FastAPI later |
| Migrations | Alembic | Teaches you migrations early — critical skill for later |
| HTTP client | httpx | Modern replacement for `requests`; async-ready for future |
| Validation | Pydantic v2 | Catches bad data at boundaries; reappears in every later project |
| Testing | pytest + pytest-cov | Industry standard |
| Env config | python-dotenv | Standard |
| Linting | Ruff | Fast, replaces flake8 + isort + more |
| Type checking | mypy (optional, recommended) | Catches bugs before runtime |
| Packaging | `pyproject.toml` with `hatchling` | Modern Python packaging |
| CI | GitHub Actions | Free, standard |

**Beginner note:** If SQLAlchemy feels overwhelming on day 1, start with raw `sqlite3` for 2 days, then migrate to SQLAlchemy. The migration itself is a useful learning exercise.

### 8.3 External API selection

You need a free API that returns USD→EGP. Evaluate and pick one as primary, one as fallback:

| API | Free tier | Needs key? | EGP supported? | Historical? | Recommended role |
|---|---|---|---|---|---|
| `open.er-api.com` | Unlimited (fair use) | No | Yes | No (only latest) | **Primary** |
| `frankfurter.app` | Unlimited | No | No (ECB rates — EGP not listed) | Yes | ❌ Skip (no EGP) |
| `exchangerate.host` | Paid now | Yes | Yes | Yes | Optional paid upgrade |
| `fawazahmed0/exchange-api` (GitHub CDN) | Unlimited | No | Yes | Yes (daily) | **Fallback** |
| Central Bank of Egypt | Public data, no formal API | No | Yes (authoritative) | Yes | Stretch goal: scrape |

**Decision:** Use `open.er-api.com/v6/latest/USD` as primary for today's rate, and `fawazahmed0/exchange-api` (hosted on jsDelivr/Cloudflare) for historical backfill. Both are keyless and free.

**Before writing code**, run this in your terminal to confirm they're up and include EGP — APIs change:

```bash
curl -s https://open.er-api.com/v6/latest/USD | jq '.rates.EGP'
curl -s https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json | jq '.usd.egp'
```

If either has changed or doesn't return EGP, search for a replacement before committing to it in code.

### 8.4 Data model

```
┌─────────────────────┐     ┌──────────────────────┐
│     categories      │     │        budgets        │
├─────────────────────┤     ├──────────────────────┤
│ id         PK       │     │ id            PK      │
│ name       UNIQUE   │     │ year_month    UNIQUE  │
│ created_at          │     │ amount_usd            │
└──────────┬──────────┘     │ created_at            │
           │                └──────────────────────┘
           │
           │ 1
           │
           │ N
┌──────────▼──────────┐     ┌──────────────────────┐
│     expenses        │     │     fx_rates          │
├─────────────────────┤     ├──────────────────────┤
│ id         PK       │     │ id            PK      │
│ amount_egp          │     │ date          UNIQUE  │
│ amount_usd (cached) │     │ usd_to_egp            │
│ fx_rate_date (FK)   │────►│ source                │
│ category_id (FK)    │     │ fetched_at            │
│ note                │     └──────────────────────┘
│ spent_at            │
│ created_at          │
└─────────────────────┘
```

**Key decisions:**

- `amount_usd` is **cached** on the expense row at insert time using that day's FX rate. This way, historical totals don't change if FX changes. This is the most important design choice in the app.
- `fx_rates.date` is a natural primary key candidate but we keep a synthetic `id` for easier FK handling.
- All monetary amounts are stored as **integers in minor units** (piastres = EGP × 100, cents = USD × 100). Floats and money never mix. This avoids floating-point drift.
- `spent_at` is a DATE (not DATETIME) — we don't care about time-of-day for expenses.
- Timestamps are stored in UTC; display converts to `Africa/Cairo` (which is EET, UTC+2, no DST since 2014).

### 8.5 File structure

```
masareef/
├── .github/
│   └── workflows/
│       └── ci.yml
├── masareef/                    # Main package
│   ├── __init__.py
│   ├── __main__.py              # Entry point: python -m masareef
│   ├── cli.py                   # Typer app; command registration
│   ├── config.py                # Settings, paths, env vars
│   ├── db.py                    # Engine, session factory
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic models (for validation)
│   ├── repositories/            # Data-access layer
│   │   ├── __init__.py
│   │   ├── expenses.py
│   │   ├── categories.py
│   │   ├── budgets.py
│   │   └── fx_rates.py
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── expense_service.py
│   │   ├── fx_service.py
│   │   ├── budget_service.py
│   │   └── report_service.py
│   ├── commands/                # One file per top-level command
│   │   ├── __init__.py
│   │   ├── add.py
│   │   ├── list_cmd.py          # 'list' is a reserved word
│   │   ├── budget.py
│   │   ├── sync_fx.py
│   │   ├── status.py
│   │   ├── alert_check.py
│   │   ├── categories.py
│   │   └── export_import.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── money.py             # Minor-unit conversions
│   │   ├── dates.py             # TZ helpers
│   │   └── display.py           # Rich tables, colors
│   └── migrations/              # Alembic migrations
│       └── versions/
├── tests/
│   ├── conftest.py              # Fixtures: temp DB, mock HTTP
│   ├── unit/
│   │   ├── test_money.py
│   │   ├── test_dates.py
│   │   ├── test_fx_service.py
│   │   └── test_budget_service.py
│   ├── integration/
│   │   ├── test_add_command.py
│   │   ├── test_status_command.py
│   │   └── test_sync_fx_command.py
│   └── data/
│       ├── sample_fx.json
│       └── sample_expenses.csv
├── docs/
│   ├── screenshots/
│   └── demo.gif
├── .gitignore
├── .env.example
├── pyproject.toml
├── alembic.ini
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## 9. Detailed command specifications

### 9.1 Command reference

```
masareef [--help] [--version]
  add AMOUNT CATEGORY [NOTE] [--date YYYY-MM-DD]
  list [--month YYYY-MM] [--category NAME] [--limit N]
  edit EXPENSE_ID [--amount X] [--category Y] [--note Z] [--date D]
  delete EXPENSE_ID [--yes]
  
  categories list
  categories add NAME
  categories rename OLD NEW
  categories delete NAME
  
  budget set AMOUNT_USD [--month YYYY-MM]
  budget show [--month YYYY-MM]
  
  sync-fx [--backfill] [--days N]
  status [--month YYYY-MM]
  alert-check [--quiet] [--threshold-warn 0.8] [--threshold-alert 1.0]
  
  export csv [--output FILE] [--month YYYY-MM]
  import csv FILE [--dry-run]
  
  db init
  db path
```

### 9.2 Example user sessions

**First-time setup:**

```bash
$ pipx install masareef
$ masareef db init
Created database at /home/ammar/.masareef/masareef.db
Seeded 8 default categories.

$ masareef sync-fx
✓ Fetched USD/EGP = 51.24 from open.er-api.com

$ masareef budget set 800
✓ Monthly budget set to $800.00 (~ EGP 40,992.00 at today's rate)
```

**Daily use:**

```bash
$ masareef add 85 transport "أوبر من البيت للنادي"
✓ Logged: EGP 85.00 ($1.66) — transport — 2026-04-23

$ masareef add 450 food "عشا مع الشباب"
✓ Logged: EGP 450.00 ($8.78) — food — 2026-04-23

$ masareef status
───────────── April 2026 ─────────────
Budget:     $800.00  (EGP 40,992 at today's rate)
Spent:      $487.23  (EGP 24,960 at historical rates)
Remaining:  $312.77  (39% left, 7 days remaining)
Daily avg:  $21.18       Projected: $656.58
Status:     🟢 On track (pacing 82% of budget)

Top categories this month:
  food         $198.12  (40.7%)
  rent         $147.00  (30.2%)
  transport    $ 58.44  (12.0%)
  utilities    $ 42.67  ( 8.8%)
  other        $ 41.00  ( 8.4%)
```

**Cron setup (in crontab):**

```cron
# Sync FX every day at 9am
0 9 * * * /home/ammar/.local/bin/masareef sync-fx >> /home/ammar/.masareef/cron.log 2>&1

# Alert check every evening at 9pm (only noisy if over 80%)
0 21 * * * /home/ammar/.local/bin/masareef alert-check
```

## 10. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Chosen FX API goes down or changes schema | Medium | High | Two independent APIs with fallback; schema validation; cached last known rate never expires (just warns) |
| User logs expense with wrong currency (thinks it's USD) | Medium | Medium | Always display EGP in the confirmation message; require explicit `--usd` flag to enter in USD (future) |
| SQLite file corruption | Low | High | WAL mode; daily automatic backup to `~/.masareef/backups/` |
| Arabic text rendering breaks in Windows terminals | High | Low | Document "use Windows Terminal or WSL"; add smoke test for UTF-8 |
| User scope-creeps into "I want charts too" | High | Low | Explicitly non-goal in v1; future version |
| User runs out of time (real beginner hazard) | High | High | Hard cut at end of week 2 even if "should" features (G8, G9) aren't done. MVP is G1–G7. |
| FX rate fetched is wrong/outlier | Low | High | Sanity check: reject any rate that's >20% different from the last known rate; require confirmation |

## 11. Success metrics (how you'll know it worked)

### 11.1 Product metrics (measured on yourself)

- **Adoption:** You use the tool ≥ 5 days in the first week post-launch.
- **Retention:** You still use it 30 days later without modification.
- **Accuracy:** Logged total matches your bank statement within 5% margin at month end.

### 11.2 Engineering metrics

- **Test coverage:** ≥ 70% (measured with `pytest --cov`)
- **CI:** 100% of pushes to main pass CI in < 3 minutes
- **Install time:** `pipx install` succeeds in < 30 seconds on a fresh machine
- **Startup time:** `masareef --help` returns in < 300ms

### 11.3 Portfolio metrics

- **GitHub:** Repo is public, README has badges (CI, license, PyPI version), at least one GIF demo
- **Blog:** One writeup published linking the repo
- **Social:** Shared on at least LinkedIn and Twitter/X
- **Bonus:** First external star on the repo (ask a friend to star it — it's fine, everyone does this)

## 12. Out of scope & future work

### 12.1 Explicitly v2 or later

- Recurring expenses (rent, Netflix, gym)
- Income tracking (earnings in USD)
- Savings goals
- Multi-currency spending (EUR, GBP, AED)
- Web dashboard (this becomes a Streamlit wrapper in Tier 2)
- Receipt photo logging (project #53)
- Natural language entry ("اتغديت بـ ٨٠ جنيه" → parsed expense) — project #66
- Bank statement import (CIB, NBE CSV formats)
- Sync across devices (SQLite → optional Postgres backend)

### 12.2 Ideas log (capture as GitHub issues, don't build now)

- Plot monthly trends with matplotlib
- Telegram bot frontend
- Custom FX rate override (for users who convert through black market)
- "What-if" calculator: "If EGP drops to 60, how does my budget change?"

---

# Part 2 — Implementation Plan

## 13. Prerequisites

Before Day 1, have these installed and verified:

```bash
# Python 3.11+
python3 --version          # should print 3.11.x or higher

# pipx (for clean global installs)
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# git with your GitHub creds set up
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main

# GitHub CLI (optional but saves time)
gh --version

# A code editor (VS Code recommended)
# Install extensions: Python, Ruff, GitLens

# Verify you can reach the APIs
curl -sS https://open.er-api.com/v6/latest/USD | head -c 200
```

**Check your terminal Arabic rendering**:
```bash
echo "مرحبا بالعالم"
```
If you see boxes or question marks, set your terminal font to one that includes Arabic (e.g., "Fira Code Nerd Font" or "Noto Sans Mono Arabic").

## 14. Milestones & weekly plan

### Week 1 — Core (15 hours)

| Day | Hours | Milestone | Deliverable |
|---|---|---|---|
| Mon | 2h | **M1: Project scaffolded** | Empty repo, `pyproject.toml`, `pre-commit`, `ruff`, a trivial `masareef --version` command |
| Tue | 3h | **M2: Database + models** | SQLAlchemy models, Alembic initial migration, `db init` command works |
| Wed | 3h | **M3: Expenses CRUD** | `add`, `list`, `delete`, `edit` commands work end-to-end |
| Thu | 3h | **M4: FX service** | `sync-fx` command with primary + fallback APIs; rates persisted |
| Fri | 2h | **M5: FX integrated into expenses** | `add` now auto-converts to USD and stores both amounts |
| Sat | 2h | **M6: Basic tests** | ≥ 10 unit tests, pytest runs clean |

**End of week 1 gate:** You should be logging your own real expenses by Saturday evening.

### Week 2 — Polish + ship (15 hours)

| Day | Hours | Milestone | Deliverable |
|---|---|---|---|
| Mon | 2h | **M7: Budgets** | `budget set/show` commands |
| Tue | 3h | **M8: Status + alerts** | `status`, `alert-check` with color output and projection math |
| Wed | 2h | **M9: Categories + export** | Full category CRUD, CSV export |
| Thu | 2h | **M10: CI + more tests** | GitHub Actions workflow, coverage badge, coverage ≥ 70% |
| Fri | 2h | **M11: Packaging + install** | `pipx install .` works locally; TestPyPI upload optional |
| Sat | 2h | **M12: README + demo** | Polished README, demo GIF, blog post draft |
| Sun | 2h | **M13: Launch** | Push to GitHub, publish blog post, share on LinkedIn |

## 15. Step-by-step setup (Day 1, first 2 hours)

### 15.1 Create the repo

```bash
mkdir -p ~/projects/masareef && cd ~/projects/masareef
git init
gh repo create masareef --public --source=. --remote=origin   # or create on github.com manually
```

### 15.2 Bootstrap the project

Create these files in this order:

**`.gitignore`**
```
__pycache__/
*.py[cod]
.venv/
venv/
.env
*.egg-info/
dist/
build/
.coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
~/.masareef/
masareef.db
*.sqlite3
```

**`pyproject.toml`**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "masareef"
version = "0.1.0"
description = "Egyptian expense tracker CLI with USD-anchored budgeting"
authors = [{name = "Ammar", email = "you@example.com"}]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.7.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "httpx>=0.27.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "respx>=0.20.0",  # for mocking httpx in tests
]

[project.scripts]
masareef = "masareef.cli:app"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "B", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=masareef --cov-report=term-missing"
```

### 15.3 Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux/Mac
# or: .venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -e ".[dev]"
```

### 15.4 Verify the trivial CLI works

Create `masareef/__init__.py` (empty) and `masareef/cli.py`:

```python
# masareef/cli.py
import typer
from rich.console import Console

app = typer.Typer(help="Masareef — Egyptian expense tracker with USD budgeting")
console = Console()

@app.command()
def version() -> None:
    """Show version."""
    from masareef import __version__
    console.print(f"masareef {__version__}")

@app.command()
def hello(name: str = "world") -> None:
    """Smoke test."""
    console.print(f"[bold green]مرحبا {name}![/bold green]")

if __name__ == "__main__":
    app()
```

And `masareef/__init__.py`:
```python
__version__ = "0.1.0"
```

Test:
```bash
masareef hello --name Ammar
# Should print a green-bold Arabic greeting
masareef version
```

Commit:
```bash
git add .
git commit -m "feat: project scaffolding with typer + rich"
git push -u origin main
```

**You have now completed M1.** Every subsequent session starts with `git pull`, `source .venv/bin/activate`, then the day's work.

## 16. Testing strategy

### 16.1 Test pyramid

- **Unit tests (~70%):** Pure functions — money conversion, date helpers, budget math, FX parsing.
- **Integration tests (~25%):** Command handlers against a temp SQLite DB with mocked HTTP.
- **Smoke tests (~5%):** A single end-to-end test that actually runs `masareef` as a subprocess.

### 16.2 Key testing patterns

**Use a temp DB fixture in `conftest.py`:**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from masareef.models import Base

@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

**Mock HTTP with `respx`:**

```python
import respx
import httpx

@respx.mock
def test_fx_fetch_primary_success():
    respx.get("https://open.er-api.com/v6/latest/USD").mock(
        return_value=httpx.Response(200, json={"rates": {"EGP": 51.24}})
    )
    rate = fx_service.fetch_today()
    assert rate == 51.24
```

**Test fallback logic:**

```python
@respx.mock
def test_fx_fallback_when_primary_fails():
    respx.get("https://open.er-api.com/v6/latest/USD").mock(
        return_value=httpx.Response(500)
    )
    respx.get(re.compile(r"https://cdn\.jsdelivr\.net/.*")).mock(
        return_value=httpx.Response(200, json={"usd": {"egp": 51.24}})
    )
    rate = fx_service.fetch_today()
    assert rate == 51.24
```

### 16.3 Coverage targets per module

| Module | Target coverage | Rationale |
|---|---|---|
| `utils/money.py` | 100% | Pure math — no excuse |
| `services/*` | ≥ 85% | Business logic — test thoroughly |
| `repositories/*` | ≥ 70% | Mostly CRUD — smoke-test |
| `commands/*` | ≥ 60% | Thin glue — integration tests cover most |
| **Overall** | **≥ 70%** | Realistic for a 2-week project |

## 17. Git workflow

### 17.1 Branching

- `main` is always green (CI passes, installable).
- Feature branches: `feat/add-command`, `fix/fx-timeout`, `docs/readme`, `test/money-edge-cases`.
- **Commit often, push daily.** Small commits > heroic commits.

### 17.2 Commit message convention (Conventional Commits)

```
feat(fx): add fallback to jsdelivr CDN API
fix(cli): handle negative amount with clear error message
test(budget): cover end-of-month projection edge case
docs(readme): add demo GIF
chore(ci): bump actions/checkout to v4
refactor(repositories): extract base repo class
```

### 17.3 PR discipline (even though you're solo)

Open a PR for every feature against `main`, even as a solo dev. It forces you to:
1. Write a PR description summarizing what changed and why.
2. See the diff in GitHub UI — catches embarrassing mistakes.
3. Wait for CI to go green before merge.
4. Creates a history recruiters can scroll through.

### 17.4 CI workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest --cov=masareef --cov-report=xml
      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: codecov/codecov-action@v4
```

## 18. Distribution

### 18.1 Option A — GitHub install (simplest, recommended for v0.1)

Users install via:
```bash
pipx install git+https://github.com/<you>/masareef
```

### 18.2 Option B — TestPyPI (teaches packaging)

```bash
pip install build twine
python -m build
python -m twine upload --repository testpypi dist/*
# Then users install:
pipx install --index-url https://test.pypi.org/simple/ --pip-args="--extra-index-url https://pypi.org/simple/" masareef
```

### 18.3 Option C — PyPI (real)

Only do this once you've used the tool for at least 2 weeks and are confident. The `masareef` name is probably available but confirm on `pypi.org/project/masareef/`.

## 19. README & portfolio finalization checklist

Your README is the single most important artifact in this project for career purposes. Recruiters scan it in ~10 seconds. It must have:

- [ ] A one-sentence headline explaining what it does and for whom
- [ ] Badges: CI status, license, Python version, (optional) PyPI version, coverage
- [ ] A demo GIF (use [asciinema](https://asciinema.org/) + [agg](https://github.com/asciinema/agg) to record terminal sessions)
- [ ] Installation instructions (one command)
- [ ] Quick-start with 3–5 example commands
- [ ] Screenshot of `status` output
- [ ] A "Why does this exist?" section with the FX devaluation chart or stat
- [ ] Architecture diagram (export the Part 1 ASCII diagram, or redraw in excalidraw.com)
- [ ] Tech stack list with links
- [ ] Contributing section (even if basic)
- [ ] License (MIT)
- [ ] A link to your blog post

### 19.1 Recording a demo GIF

```bash
# Install asciinema
pip install asciinema
# Record
asciinema rec demo.cast
# ... run your commands ...
# Ctrl-D to stop
# Convert to GIF (install agg first)
agg demo.cast demo.gif --theme monokai --font-size 16
```

Put `demo.gif` in `docs/` and reference it at the top of your README.

### 19.2 Blog post outline (600–1000 words)

1. **Hook** (100 words): "I earn in dollars and spend in pounds, and for two years I couldn't tell if I was overspending or just experiencing inflation…"
2. **Problem** (200 words): The EGP devaluation data, why existing tools fail.
3. **Solution** (200 words): What Masareef does, with the `status` screenshot.
4. **Design decisions** (200 words): Why CLI, why SQLite, why cache historical rates.
5. **What I learned** (200 words): Honest — what was hard, what you'd do differently.
6. **Call to action** (100 words): Link to GitHub, invite issues/PRs.

## 20. Learning resources (curated, in the order you'll need them)

| Week/Day | Topic | Resource |
|---|---|---|
| Day 1 | Typer basics | Official docs — https://typer.tiangolo.com/tutorial/ |
| Day 1 | Rich tables & color | https://rich.readthedocs.io/en/stable/tables.html |
| Day 2 | SQLAlchemy 2.0 ORM | Official tutorial — https://docs.sqlalchemy.org/en/20/tutorial/ |
| Day 2 | Alembic migrations | https://alembic.sqlalchemy.org/en/latest/tutorial.html |
| Day 3 | Pydantic v2 | https://docs.pydantic.dev/latest/ |
| Day 4 | httpx async & mocking | https://www.python-httpx.org/ + respx docs |
| Day 4 | Decimal vs float for money | Search: "Python decimal module money" |
| Day 6 | pytest fixtures | https://docs.pytest.org/en/stable/fixture.html |
| Week 2 Day 4 | GitHub Actions | https://docs.github.com/en/actions/quickstart |
| Week 2 Day 5 | Python packaging 2024 | https://packaging.python.org/en/latest/tutorials/packaging-projects/ |

## 21. Common pitfalls to avoid

1. **Scope creep.** Every time you think "it would be nice if…", write it as a GitHub issue labeled `future` and close the thought. v1 is v1.
2. **Over-engineering on day 1.** Don't set up Docker, don't add Redis, don't reach for Celery. SQLite is enough.
3. **Skipping tests "because it's small".** Test coverage below 50% means the repo looks amateur to recruiters.
4. **Committing secrets.** Put `.env` in `.gitignore` from day 1, even though v1 has no secrets. Build the habit.
5. **Perfectionism on README.** Ship a 60% README in week 2, iterate it for 30 minutes every week forever.
6. **Not dogfooding.** If you don't use your own tool for a week before publishing, you will have shipped broken UX and not noticed.
7. **Using floats for money.** `0.1 + 0.2 != 0.3` in Python. Store as integer piastres/cents.
8. **Calling live APIs in tests.** Your tests must work offline. Mock everything external with respx.
9. **Forgetting timezones.** Africa/Cairo is UTC+2 year-round since 2014 — but store UTC, display Cairo. Test the midnight edge case.
10. **Missing the "why" in the README.** A good README opens with the *problem*, not the *features*.

## 22. Stretch goals (only if week 2 goes fast)

These are "would be nice but don't gate success":

- [ ] Weekly summary email via a `masareef digest --email` subcommand (use SMTP via Gmail app password)
- [ ] ASCII bar chart in `status` using Rich's Bar widget
- [ ] `masareef search <query>` — full-text search over notes (SQLite FTS5)
- [ ] Colored `list` output where food = green, rent = red, etc.
- [ ] `masareef import cib-statement.pdf` — parse CIB bank statement PDFs (requires pdfplumber)
- [ ] Dark/light theme support via `MASAREEF_THEME` env var
- [ ] Shell completion: `masareef --install-completion bash`

---

# Part 3 — Definition of Done

Masareef v0.1.0 is **DONE** when:

**Functional**
- [ ] All Must-priority user stories (US-1 through US-8) pass their acceptance criteria
- [ ] You have used it daily for 7 consecutive days

**Engineering**
- [ ] `pytest` passes with ≥ 70% coverage
- [ ] `ruff check .` is clean
- [ ] CI is green on `main`
- [ ] `pipx install git+https://github.com/<you>/masareef` succeeds on a clean machine
- [ ] `masareef --help` renders correctly in Bash, Zsh, and WSL

**Portfolio**
- [ ] Public GitHub repo with polished README
- [ ] Demo GIF embedded at the top of the README
- [ ] CI, license, and coverage badges
- [ ] At least 3 closed GitHub issues (even if you opened them yourself — shows process)
- [ ] A tagged release (`v0.1.0`) with release notes
- [ ] A blog post published linking the repo
- [ ] Post shared on LinkedIn and Twitter/X

**Next step:** Once Masareef is shipped, move directly to project #2 in the roadmap — **Mokhaleset**, the FastAPI + Postgres task API. It reuses Masareef's SQLAlchemy models, Pydantic validation, and Git/CI muscle memory — so you'll ship it twice as fast.

---

*End of document. Last updated: 2026-04-23. License: you own this document; use it however you want.*
