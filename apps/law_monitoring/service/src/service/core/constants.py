"""Constants for the law monitoring service."""

# Database schema configuration
SCHEMA_PREFIX = "law_monitoring"
DEFAULT_SCHEMA = "public"

# Alembic configuration
VERSION_TABLE_NAME = "alembic_version_law_monitoring"


def get_tenant_schema_name(tenant_id: str | None) -> str:
    """Get the schema name for a given tenant ID.

    Args:
        tenant_id: The tenant identifier, or None for default schema

    Returns:
        Schema name: either 'law_monitoring_{tenant_id}' or 'public'
    """
    return f"{SCHEMA_PREFIX}_{tenant_id}" if tenant_id else DEFAULT_SCHEMA
