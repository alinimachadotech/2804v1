"""MariaDB connection helpers for CADUP Hub."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tools.cadup_hub.config import CadupConfig, load_config


ConnectionFactory = Callable[[], Any]


def get_connection(config: CadupConfig | None = None):
    """Create a PyMySQL connection without logging credentials."""
    import pymysql

    cfg = config or load_config()
    return pymysql.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_user,
        password=cfg.db_password,
        database=cfg.db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

