from __future__ import annotations

from contextlib import AbstractContextManager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session

from masareef import __version__
from masareef.db import init_db, session_scope
from masareef.services import budgets, categories, fx
from masareef.services.csv_io import export_expenses_csv, import_expenses_csv
from masareef.services.expenses import (
    add_expense,
    delete_expense,
    fix_expense_rate,
    list_expenses,
    update_expense,
)
from masareef.services.reports import alert_exit_code, build_status_report
from masareef.utils.dates import month_key, parse_date, today_cairo
from masareef.utils.money import format_egp, format_usd

app = typer.Typer(help="Masareef: local EGP expense tracking with USD budgeting.")
db_app = typer.Typer(help="Database commands.")
budget_app = typer.Typer(help="Budget commands.")
categories_app = typer.Typer(help="Category commands.")
export_app = typer.Typer(help="Export commands.")
import_app = typer.Typer(help="Import commands.")

app.add_typer(db_app, name="db")
app.add_typer(budget_app, name="budget")
app.add_typer(categories_app, name="categories")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")

console = Console()


def _open_session() -> AbstractContextManager[Session]:
    init_db()
    return session_scope()


def _parse_positive_decimal(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise typer.BadParameter("Amount must be a number.") from exc
    if amount <= 0:
        raise typer.BadParameter("Amount must be greater than zero.")
    return amount


@app.command()
def version() -> None:
    """Show the installed Masareef version."""
    console.print(f"masareef {__version__}")


@db_app.command("init")
def init_database() -> None:
    """Create local database tables and seed default categories."""
    init_db()
    with _open_session() as session:
        categories.seed_default_categories(session)
    console.print("[green]Database initialized.[/green]")


@categories_app.command("list")
def list_categories() -> None:
    """Show all spending categories."""
    with _open_session() as session:
        rows = categories.list_categories(session)
    table = Table(title="Categories")
    table.add_column("Name")
    for category in rows:
        table.add_row(category.name)
    console.print(table)


@categories_app.command("add")
def add_category(name: str) -> None:
    """Create a spending category."""
    with _open_session() as session:
        try:
            category = categories.add_category(session, name)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
    console.print(f"[green]Added category:[/green] {category.name}")


@categories_app.command("rename")
def rename_category(old: str, new: str) -> None:
    """Rename a spending category."""
    with _open_session() as session:
        try:
            category = categories.rename_category(session, old, new)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
    console.print(f"[green]Renamed category:[/green] {category.name}")


@app.command()
def sync_fx(
    backfill: bool = typer.Option(False, "--backfill", help="Fetch missing rates for recent days."),
    days: int = typer.Option(90, "--days", min=1, max=365, help="Number of days to backfill."),
) -> None:
    """Fetch and cache today's USD/EGP exchange rate."""
    with _open_session() as session:
        try:
            if backfill:
                rates = fx.sync_missing_rates(session, days=days)
            else:
                rate = fx.sync_today_rate(session)
        except RuntimeError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
    if backfill:
        console.print(f"[green]Backfilled[/green] {len(rates)} missing FX rate(s).")
        return
    console.print(
        f"[green]Synced[/green] USD/EGP = {rate.egp_per_usd} "
        f"for {rate.rate_date.isoformat()} from {rate.source}"
    )


@app.command()
def add(
    amount: str = typer.Argument(..., help="Expense amount in EGP."),
    category: str = typer.Argument(..., help="Category name."),
    note: str = typer.Argument("", help="Optional note."),
    date_text: str | None = typer.Option(None, "--date", help="Expense date as YYYY-MM-DD."),
) -> None:
    """Log an EGP expense and store its USD value using a cached historical FX rate."""
    amount_decimal = _parse_positive_decimal(amount)
    try:
        spent_on = parse_date(date_text)
    except ValueError as exc:
        raise typer.BadParameter("Date must use YYYY-MM-DD format.") from exc

    with _open_session() as session:
        try:
            expense, rate_lookup = add_expense(session, amount_decimal, category, note, spent_on)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc

    if rate_lookup.is_stale:
        console.print(
            f"[yellow]Warning:[/yellow] {fx.stale_rate_message(rate_lookup.rate, spent_on)}"
        )
    console.print(
        f"[green]Logged[/green] #{expense.id}: {format_egp(expense.amount_egp_piastres)} "
        f"({format_usd(expense.amount_usd_cents)}) - {category} - {spent_on.isoformat()}"
    )


@app.command()
def edit(
    expense_id: int = typer.Argument(..., help="Expense ID to edit."),
    amount: str | None = typer.Option(None, "--amount", help="New amount in EGP."),
    category: str | None = typer.Option(None, "--category", help="New category name."),
    note: str | None = typer.Option(None, "--note", help="New note."),
    date_text: str | None = typer.Option(None, "--date", help="New date as YYYY-MM-DD."),
) -> None:
    """Edit an expense and recalculate USD if amount or date changes."""
    if amount is None and category is None and note is None and date_text is None:
        console.print("[yellow]Nothing to edit.[/yellow]")
        raise typer.Exit(1)

    amount_decimal = _parse_positive_decimal(amount) if amount is not None else None
    try:
        spent_on = parse_date(date_text) if date_text is not None else None
    except ValueError as exc:
        raise typer.BadParameter("Date must use YYYY-MM-DD format.") from exc

    with _open_session() as session:
        try:
            expense, rate_lookup = update_expense(
                session,
                expense_id,
                amount_egp=amount_decimal,
                category_name=category,
                note=note,
                spent_on=spent_on,
            )
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc

    if rate_lookup is not None and rate_lookup.is_stale:
        console.print(
            f"[yellow]Warning:[/yellow] "
            f"{fx.stale_rate_message(rate_lookup.rate, expense.spent_on)}"
        )
    console.print(
        f"[green]Updated[/green] #{expense.id}: {format_egp(expense.amount_egp_piastres)} "
        f"({format_usd(expense.amount_usd_cents)})"
    )


@app.command()
def delete(
    expense_id: int = typer.Argument(..., help="Expense ID to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete an expense."""
    if not yes and not typer.confirm(f"Delete expense #{expense_id}?"):
        raise typer.Exit(1)

    with _open_session() as session:
        try:
            expense = delete_expense(session, expense_id)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
    console.print(
        f"[green]Deleted[/green] #{expense.id}: {format_egp(expense.amount_egp_piastres)}"
    )


@app.command("fix-rate")
def fix_rate(expense_id: int = typer.Argument(..., help="Expense ID to recalculate.")) -> None:
    """Recalculate an expense using the cached FX rate for its date."""
    with _open_session() as session:
        try:
            expense = fix_expense_rate(session, expense_id)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
    console.print(
        f"[green]Fixed[/green] #{expense.id}: {format_usd(expense.amount_usd_cents)} "
        f"at USD/EGP {expense.fx_rate}"
    )


@app.command("list")
def list_command(
    month: str | None = typer.Option(None, "--month", help="Filter by month, e.g. 2026-04."),
    category: str | None = typer.Option(None, "--category", help="Filter by category."),
    limit: int = typer.Option(20, "--limit", min=1, max=500, help="Maximum rows to show."),
) -> None:
    """List recent expenses."""
    with _open_session() as session:
        rows = list_expenses(session, limit=limit, month=month, category_name=category)

    table = Table(title="Expenses")
    table.add_column("ID", justify="right")
    table.add_column("Date")
    table.add_column("Category")
    table.add_column("EGP", justify="right")
    table.add_column("USD", justify="right")
    table.add_column("Note")
    for expense in rows:
        table.add_row(
            str(expense.id),
            expense.spent_on.isoformat(),
            expense.category.name,
            format_egp(expense.amount_egp_piastres),
            format_usd(expense.amount_usd_cents),
            expense.note,
        )
    console.print(table)


@export_app.command("csv")
def export_csv(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output CSV path.")],
    month: str | None = typer.Option(None, "--month", help="Filter by month, e.g. 2026-04."),
) -> None:
    """Export expenses to CSV."""
    with _open_session() as session:
        count = export_expenses_csv(session, output, month=month)
    console.print(f"[green]Exported[/green] {count} expense(s) to {output}")


@import_app.command("csv")
def import_csv(input_path: Annotated[Path, typer.Argument(help="Input CSV path.")]) -> None:
    """Import expenses from a Masareef CSV export."""
    with _open_session() as session:
        try:
            result = import_expenses_csv(session, input_path)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc

    console.print(
        f"[green]Imported[/green] {result.imported} expense(s); "
        f"skipped {result.skipped} row(s)."
    )
    for error in result.errors[:10]:
        console.print(f"[yellow]{error}[/yellow]")


@budget_app.command("set")
def set_budget(
    amount: str = typer.Argument(..., help="Monthly budget amount in USD."),
    month: str | None = typer.Option(
        None, "--month", help="Optional month override, e.g. 2026-04."
    ),
) -> None:
    """Set the default or month-specific USD budget."""
    amount_decimal = _parse_positive_decimal(amount)
    with _open_session() as session:
        budget = budgets.set_budget(session, amount_decimal, month)
    scope = budget.month or "default monthly"
    console.print(f"[green]Set {scope} budget:[/green] {format_usd(budget.amount_usd_cents)}")


@budget_app.command("show")
def show_budget(
    month: str | None = typer.Option(None, "--month", help="Month to inspect, e.g. 2026-04."),
) -> None:
    """Show the effective budget for a month."""
    target_month = month or month_key(today_cairo())
    with _open_session() as session:
        budget = budgets.get_effective_budget(session, target_month)
        rate = fx.get_cached_rate(session, today_cairo()) or fx.get_latest_cached_rate(session)

    if budget is None:
        console.print("[yellow]No budget set.[/yellow]")
        raise typer.Exit(1)

    line = f"Budget for {target_month}: {format_usd(budget.amount_usd_cents)}"
    if rate is not None:
        egp_piastres = round((budget.amount_usd_cents / 100) * float(rate.egp_per_usd) * 100)
        line += f" (~{format_egp(egp_piastres)} at {rate.egp_per_usd})"
    console.print(line)


@app.command()
def status() -> None:
    """Show current-month spending status."""
    with _open_session() as session:
        report = build_status_report(session)

    table = Table(title=f"Status: {report.month}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row(
        "Spent",
        f"{format_usd(report.spent_usd_cents)} / {format_egp(report.spent_egp_piastres)}",
    )
    if report.budget_usd_cents is not None:
        budget_text = format_usd(report.budget_usd_cents)
        if report.budget_egp_piastres_today is not None:
            budget_text += f" / ~{format_egp(report.budget_egp_piastres_today)}"
        table.add_row("Budget", budget_text)
        table.add_row("Used", f"{report.percent_used:.1f}%")
    else:
        table.add_row("Budget", "Not set")
    table.add_row("Days remaining", str(report.days_remaining))
    table.add_row("Projected", format_usd(report.projected_usd_cents))
    console.print(table)

    if report.categories:
        category_table = Table(title="Top Categories")
        category_table.add_column("Category")
        category_table.add_column("USD", justify="right")
        for name, total in report.categories[:5]:
            category_table.add_row(name, format_usd(total))
        console.print(category_table)


@app.command("alert-check")
def alert_check(
    quiet: bool = typer.Option(False, "--quiet", help="Only use the exit code."),
    warn_threshold: float = typer.Option(
        80.0, "--warn-threshold", help="Warning threshold percent."
    ),
    alert_threshold: float = typer.Option(
        100.0, "--alert-threshold", help="Alert threshold percent."
    ),
) -> None:
    """Cron-friendly budget alert check."""
    with _open_session() as session:
        report = build_status_report(session)
    exit_code = alert_exit_code(report, alert_threshold=alert_threshold)

    if not quiet and report.percent_used is not None and report.percent_used >= warn_threshold:
        style = "red" if exit_code == 2 else "yellow"
        console.print(
            f"[{style}]Budget usage is {report.percent_used:.1f}% "
            f"({format_usd(report.spent_usd_cents)} spent).[/{style}]"
        )
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
