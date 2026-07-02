# I Built Masareef to Budget in Dollars While Spending in Egyptian Pounds

I earn and think about long-term money in dollars, but daily life in Egypt happens in pounds. That split sounds simple until the exchange rate moves. A grocery run, a ride, rent, or dinner out can feel expensive or cheap in EGP while telling a different story in USD. After a few devaluation cycles, the mental math stops being reliable.

Masareef is a small command-line tool I built to make that daily accounting honest. It logs expenses in EGP, stores the USD value using the exchange rate from the transaction date, and compares the month against a USD-denominated budget.

The core problem is historical context. If I spend EGP 450 today and the rate is 50 EGP/USD, that is about $9. If I look back later when the rate has moved, converting that old transaction at the new rate gives the wrong picture. Expense tools that only use the current exchange rate make past months drift. Masareef avoids that by caching FX rates per day and storing the converted USD amount at the moment the expense is logged.

The first version is deliberately local and boring: Python, Typer, Rich, SQLAlchemy, and SQLite. There is no cloud sync, no account system, no mobile UI, and no analytics. That constraint is the point. I wanted a tool that can run from a terminal, work offline, and keep my personal finance data on my machine.

The daily flow looks like this:

```bash
masareef sync-fx
masareef budget set 800
masareef add 450 food "dinner"
masareef status
```

The `status` command shows how much I have spent in EGP and USD, how much of the USD budget is used, how many days remain in the month, and a simple projection based on the current daily average. There is also a cron-friendly `alert-check` command that exits with a different status code when spending crosses the alert threshold.

The most important design decision was to store money in minor units. EGP amounts are stored as piastres and USD amounts as cents. Floating point bugs are easy to dismiss in toy examples, but finance code should not depend on `0.1 + 0.2` behaving like decimal money. Python's `Decimal` handles conversion and rounding at the edges; SQLite stores the final integer amounts.

The second important decision was offline behavior. If today's FX rate is cached, logging an expense is fast. If it is not cached, Masareef tries to fetch it. If the network is down, it falls back to the latest cached rate and prints a stale-rate warning. Later, after syncing the correct historical rate, `masareef fix-rate <expense-id>` recalculates the expense.

I also added CSV export and import early. That makes the database less precious: I can back it up, inspect it in a spreadsheet, or move data between machines without inventing a sync product too soon.

This project is intentionally small, but it covers a lot of real engineering surface area: packaging, CLI ergonomics, database modeling, HTTP fallback logic, test isolation, GitHub Actions, coverage gates, and install verification with `pipx`. The test suite currently runs with a coverage threshold so the project cannot quietly regress below the quality bar I set in the PRD.

The repo is here: https://github.com/ammarkhattab/masareef

Masareef is now tagged as `v0.1.0` and installable from GitHub with `pipx install git+https://github.com/ammarkhattab/masareef.git`. Next, I want to dogfood it for a full week. That will probably surface awkward command names, missing flags, and edge cases that only show up when the tool is used at the end of a normal day. After that, I will decide whether publishing to TestPyPI or PyPI is worth it for this first version.
