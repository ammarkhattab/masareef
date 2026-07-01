from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from masareef.db import init_db, reset_engine, session_scope
from masareef.services.categories import seed_default_categories


@pytest.fixture(autouse=True)
def isolated_home(request, monkeypatch):
    root = Path.cwd() / ".pytest-data"
    name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", request.node.nodeid)
    home = root / name
    if home.exists():
        shutil.rmtree(home)
    home.mkdir(parents=True)
    monkeypatch.setenv("MASAREEF_HOME", str(home))
    reset_engine()
    init_db()
    with session_scope() as session:
        seed_default_categories(session)
    yield home
    reset_engine()
    if home.exists():
        shutil.rmtree(home)


@pytest.fixture
def db_session():
    with session_scope() as session:
        yield session


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
