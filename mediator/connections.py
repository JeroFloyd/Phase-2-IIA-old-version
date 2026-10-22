from __future__ import annotations

from typing import Any, Sequence
import mysql.connector
from mysql.connector import Error

from .config import SourceConfig


def _connect(config: SourceConfig):
    return mysql.connector.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        connection_timeout=5,
    )


def fetch_one(config: SourceConfig, item_code: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Execute the configured per-item query against one source."""
    return fetch_rows(config, config.item_sql, (item_code,))


def fetch_rows(
    config: SourceConfig,
    sql: str,
    params: Sequence[Any] = (),
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Execute a constant, application-authored SELECT with bound parameters."""
    conn = None
    cursor = None
    try:
        conn = _connect(config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return rows, {
            "source": config.name,
            "database": config.database,
            "host": config.host,
            "port": config.port,
            "status": "success",
            "rows": len(rows),
        }
    except Error as exc:
        return [], {
            "source": config.name,
            "database": config.database,
            "host": config.host,
            "port": config.port,
            "status": "error",
            "rows": 0,
            "error": str(exc),
        }
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def execute_write(
    config: SourceConfig,
    sql: str,
    params: Sequence[Any] = (),
) -> dict[str, Any]:
    """Execute one application-authored INSERT/UPDATE against its target table."""
    conn = None
    cursor = None
    try:
        conn = _connect(config)
        conn.start_transaction()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        return {
            "source": config.name,
            "database": config.database,
            "host": config.host,
            "port": config.port,
            "status": "success",
            "rowcount": cursor.rowcount,
            "lastrowid": cursor.lastrowid,
        }
    except Error as exc:
        if conn is not None and conn.is_connected():
            conn.rollback()
        return {
            "source": config.name,
            "database": config.database,
            "host": config.host,
            "port": config.port,
            "status": "error",
            "error": str(exc),
        }
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
