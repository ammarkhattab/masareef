from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
PIASTRE = Decimal("0.01")


def to_decimal(value: float | int | str | Decimal) -> Decimal:
    return Decimal(str(value))


def egp_to_piastres(value: float | int | str | Decimal) -> int:
    amount = to_decimal(value)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def usd_to_cents(value: float | int | str | Decimal) -> int:
    amount = to_decimal(value)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def piastres_to_egp(value: int) -> Decimal:
    return (Decimal(value) / 100).quantize(PIASTRE)


def cents_to_usd(value: int) -> Decimal:
    return (Decimal(value) / 100).quantize(CENT)


def egp_piastres_to_usd_cents(egp_piastres: int, egp_per_usd: Decimal) -> int:
    if egp_per_usd <= 0:
        raise ValueError("FX rate must be greater than zero.")
    egp = piastres_to_egp(egp_piastres)
    usd = egp / egp_per_usd
    return int((usd * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_egp(piastres: int) -> str:
    return f"EGP {piastres_to_egp(piastres):,.2f}"


def format_usd(cents: int) -> str:
    return f"${cents_to_usd(cents):,.2f}"
