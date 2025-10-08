import os
from logging.config import fileConfig

from sqlalchemy import text
from sqlalchemy.engine import Connection

from alembic import context
from service.core.constants import DEFAULT_SCHEMA, VERSION_TABLE_NAME
from service.core.database.database_manager import DatabaseManager
from service.core.database.models import Base  # noqa: E402
from service.dependencies import with_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def _get_database_url() -> str:
    settings = with_settings()
    db_url = str(settings.database_url.get_secret_value())
    return DatabaseManager.sanitize_database_url(db_url)


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Use tenant schema if provided, otherwise default to "public"
# Using "public" as default is standard for PostgreSQL
TENANT_SCHEMA = os.environ.get("TENANT_SCHEMA", DEFAULT_SCHEMA)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=_get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE_NAME,
        version_table_schema=TENANT_SCHEMA,
        include_schemas=True,  # Important for multi-schema support
    )
    with context.begin_transaction():
        context.run_migrations()


def _migrate_version_table_if_needed(connection: Connection) -> None:
    """Migrate from old alembic_version to new custom version table.

    This handles backward compatibility for existing deployments that used
    the default 'alembic_version' table name before multi-tenancy was added.

    TODO: Remove this function once all deployments have been migrated to the new
    version table name (alembic_version_law_monitoring). This is temporary migration
    code for backward compatibility. Safe to remove after confirming all production
    environments have been upgraded.
    """
    OLD_VERSION_TABLE = "alembic_version"

    # Check if old version table exists in this schema
    old_table_exists = connection.execute(
        text(
            "SELECT EXISTS ("
            "SELECT FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :table_name"
            ")"
        ),
        {"schema": TENANT_SCHEMA, "table_name": OLD_VERSION_TABLE},
    ).scalar()

    # Check if new version table exists
    new_table_exists = connection.execute(
        text(
            "SELECT EXISTS ("
            "SELECT FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :table_name"
            ")"
        ),
        {"schema": TENANT_SCHEMA, "table_name": VERSION_TABLE_NAME},
    ).scalar()

    # If old table exists but new one doesn't, rename it
    if old_table_exists and not new_table_exists:
        from loguru import logger

        logger.info(
            f"Migrating version table: {OLD_VERSION_TABLE} → {VERSION_TABLE_NAME}"
        )
        connection.execute(
            text(f'ALTER TABLE "{OLD_VERSION_TABLE}" RENAME TO "{VERSION_TABLE_NAME}"')
        )
        connection.commit()
        logger.info("Version table migration complete")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create a simple, standard engine for migrations
    # This avoids using the PostgresRepository which has its own schema-setting logic
    # that can conflict with Alembic's context.
    connectable = DatabaseManager.create_engine_from_url(_get_database_url())

    # Create the schema first, outside of the main migration transaction
    # Extract tenant_id from TENANT_SCHEMA for proper handling
    settings = with_settings()
    DatabaseManager.ensure_schema_exists(
        engine=connectable, tenant_id=settings.tenant_id
    )

    with connectable.connect() as connection:
        # Set search path for this connection - use identifier quoting
        connection.execute(text(f'SET search_path TO "{TENANT_SCHEMA}"'))

        # Migrate version table if upgrading from pre-multitenancy version
        # TODO: Remove this call once all deployments are migrated (see function docstring)
        _migrate_version_table_if_needed(connection)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transactional_ddl=True,  # Enable transactional DDL for atomic rollback protection
            version_table=VERSION_TABLE_NAME,
            version_table_schema=TENANT_SCHEMA,
        )

        # Run migrations - transaction is handled automatically by Alembic
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
