from __future__ import annotations

import pytest

from masareef.services.categories import add_category, list_categories, rename_category


def test_add_and_rename_category(db_session) -> None:
    add_category(db_session, "coffee")
    rename_category(db_session, "coffee", "cafes")

    names = [category.name for category in list_categories(db_session)]

    assert "cafes" in names
    assert "coffee" not in names


def test_duplicate_category_is_rejected(db_session) -> None:
    with pytest.raises(ValueError, match="already exists"):
        add_category(db_session, "food")
