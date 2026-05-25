"""Environment configuration for the isolated CADUP Hub CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CadupConfig:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    @property
    def has_credentials(self) -> bool:
        return bool(self.db_user and self.db_password)


def _parse_port(value: str | None) -> int:
    if not value:
        return 3306
    try:
        return int(value)
    except ValueError:
        return 3306


def load_config() -> CadupConfig:
    return CadupConfig(
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=_parse_port(os.getenv("DB_PORT")),
        db_user=os.getenv("DB_USER", ""),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_name=os.getenv("DB_NAME", "cadup_hub"),
    )

