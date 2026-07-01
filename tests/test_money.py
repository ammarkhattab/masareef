from __future__ import annotations

from decimal import Decimal

import pytest

from masareef.utils.money import (
    cents_to_usd,
    egp_piastres_to_usd_cents,
    egp_to_piastres,
    piastres_to_egp,
    usd_to_cents,
)


def test_money_minor_unit_conversions() -> None:
    assert egp_to_piastres("450.55") == 45055
    assert usd_to_cents("12.34") == 1234
    assert piastres_to_egp(45055) == Decimal("450.55")
    assert cents_to_usd(1234) == Decimal("12.34")


def test_egp_to_usd_uses_decimal_rate() -> None:
    assert egp_piastres_to_usd_cents(45000, Decimal("50")) == 900


def test_negative_amount_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        egp_to_piastres("-1")
