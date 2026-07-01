from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    home: Path
    db_path: Path


def get_config() -> AppConfig:
    home = Path(os.environ.get("MASAREEF_HOME", Path.home() / ".masareef")).expanduser()
    return AppConfig(home=home, db_path=home / "masareef.db")
