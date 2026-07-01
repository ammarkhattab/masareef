from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from masareef.models import Category

DEFAULT_CATEGORIES = (
    "food",
    "transport",
    "rent",
    "utilities",
    "entertainment",
    "health",
    "shopping",
    "other",
)


def seed_default_categories(session: Session) -> None:
    existing = set(session.scalars(select(Category.name)).all())
    for name in DEFAULT_CATEGORIES:
        if name not in existing:
            session.add(Category(name=name))
    session.commit()


def list_categories(session: Session) -> list[Category]:
    seed_default_categories(session)
    return list(session.scalars(select(Category).order_by(Category.name)).all())


def get_category(session: Session, name: str) -> Category | None:
    seed_default_categories(session)
    return session.scalar(select(Category).where(Category.name == name))


def add_category(session: Session, name: str) -> Category:
    normalized = normalize_category_name(name)
    if get_category(session, normalized) is not None:
        raise ValueError(f"Category '{normalized}' already exists.")
    category = Category(name=normalized)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def rename_category(session: Session, old_name: str, new_name: str) -> Category:
    category = get_category(session, normalize_category_name(old_name))
    if category is None:
        raise ValueError(f"Category '{old_name}' not found.")
    normalized_new_name = normalize_category_name(new_name)
    if get_category(session, normalized_new_name) is not None:
        raise ValueError(f"Category '{normalized_new_name}' already exists.")
    category.name = normalized_new_name
    session.commit()
    session.refresh(category)
    return category


def normalize_category_name(name: str) -> str:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("Category name cannot be empty.")
    if " " in normalized:
        raise ValueError("Category name cannot contain spaces.")
    return normalized
