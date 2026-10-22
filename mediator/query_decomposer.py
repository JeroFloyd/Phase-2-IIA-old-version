from __future__ import annotations

from typing import Any

from .config import SOURCES


def decompose_item_history_query(item_code: str) -> list[dict[str, Any]]:
    """Represent the global query as five source-specific subqueries.

    The global relation is ItemHistory; the actual source relations are the
    five local views. The decomposition pushes the ItemCode predicate to each
    relevant source using that source's local identifier.
    """
    plan = []
    for key, source in SOURCES.items():
        normalized_sql = " ".join(source.item_sql.split())
        plan.append({
            "source_key": key,
            "source": source.name,
            "database": source.database,
            "sql": normalized_sql,
            "parameter": item_code,
        })
    return plan
