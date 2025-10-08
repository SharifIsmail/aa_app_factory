"""Seed company and teams from storage

Revision ID: 2641f1afb993
Revises: 44a161304b00
Create Date: 2025-09-10 10:00:00.000000

"""

from __future__ import annotations

from typing import Any, Sequence, Union

import sqlalchemy as sa
from sqlalchemy import Connection

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2641f1afb993"
down_revision: Union[str, Sequence[str], None] = "44a161304b00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_connection() -> Connection:
    return op.get_bind()


def _table_names() -> dict[str, str]:
    prefix = "law_monitoring_"
    return {
        "company_config": f"{prefix}company_config",
        "teams": f"{prefix}teams",
    }


def _row_count(table_name: str) -> int:
    conn = _get_connection()
    result = conn.execute(sa.text(f"SELECT COUNT(*) FROM {table_name}"))
    return int(result.scalar_one())


def _load_storage_config() -> dict[str, Any] | None:
    """Attempt to load JSON config from the configured storage backend.

    We import late to avoid hard dependency during migration loading.
    Returns a dict with keys: company_description, teams (list) or None if no file.
    """
    try:
        from service.law_core.persistence.storage_factory import (
            get_configured_storage_backend,
        )

        storage = get_configured_storage_backend()
        folder = "config"
        filename = "company.json"
        if not storage.file_exists(folder, filename):
            return None

        content = storage.load_file(folder, filename)
        if not content:
            return None
        if isinstance(content, (bytes, bytearray)):
            text = content.decode("utf-8")
        else:
            text = content

        import json

        return json.loads(text)
    except Exception:
        # Storage might not be configured in this environment; ignore
        return None


def _default_config() -> dict[str, Any]:
    from service.law_core.defaults.default_company_config import (
        get_default_company_config,
    )

    cfg = get_default_company_config()
    return cfg.model_dump()


def _insert_config_and_teams(config_dict: dict[str, Any]) -> None:
    tables = _table_names()
    conn = _get_connection()

    # Insert company_config
    desc = config_dict.get("company_description")
    result = conn.execute(
        sa.text(
            f"INSERT INTO {tables['company_config']} (company_description) VALUES (:desc) RETURNING id"
        ),
        {"desc": desc},
    )
    company_id = int(result.scalar_one())

    teams = config_dict.get("teams") or []
    stmt = sa.text(
        f"""
        INSERT INTO {tables["teams"]} (
            company_id, name, description, department, daily_processes, relevant_laws_or_topics
        ) VALUES (
            :company_id, :name, :description, :department, :daily_processes, :relevant_laws_or_topics
        )
        """
    ).bindparams(sa.bindparam("daily_processes", type_=sa.JSON))

    for team in teams:
        params = {
            "company_id": company_id,
            "name": team.get("name"),
            "description": team.get("description"),
            "department": team.get("department"),
            "daily_processes": team.get("daily_processes") or [],
            "relevant_laws_or_topics": team.get("relevant_laws_or_topics"),
        }
        conn.execute(stmt, params)


def upgrade() -> None:
    tables = _table_names()

    # If any config exists, do nothing (idempotent)
    if _row_count(tables["company_config"]) > 0:
        return

    config_dict = _load_storage_config()
    if config_dict is None:
        # No storage file found. Do not seed defaults in migration.
        # Service will persist defaults on first access instead.
        return

    # Ensure well-formed structure
    if "teams" not in config_dict:
        config_dict["teams"] = []

    _insert_config_and_teams(config_dict)


def downgrade() -> None:
    tables = _table_names()
    conn = _get_connection()

    # Only perform a clean rollback if we have exactly one company_config row
    if _row_count(tables["company_config"]) != 1:
        return

    # Fetch the only company id
    res = conn.execute(sa.text(f"SELECT id FROM {tables['company_config']}"))
    company_id = int(res.scalar_one())

    # Delete dependent teams
    conn.execute(
        sa.text(f"DELETE FROM {tables['teams']} WHERE company_id = :cid"),
        {"cid": company_id},
    )
    # Delete the single company config row
    conn.execute(
        sa.text(f"DELETE FROM {tables['company_config']} WHERE id = :cid"),
        {"cid": company_id},
    )
