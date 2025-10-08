"""Database management utilities for schema creation and configuration.

LAYER: Infrastructure / Startup Operations
==========================================

This module provides LOW-LEVEL, STATELESS utilities for database infrastructure
management. It is primarily used during application startup, migrations, and
one-time setup operations.

When to use DatabaseManager:
- Application startup (main.py lifespan)
- Alembic migrations (env.py)
- Schema creation and validation
- Database URL sanitization
- One-time connection testing

When NOT to use DatabaseManager:
- Runtime query execution (use PostgresRepository instead)
- Transaction management (use PostgresRepository instead)
- Session management (use PostgresRepository instead)

Relationship to PostgresRepository:
- DatabaseManager: Stateless utilities for setup/infrastructure
- PostgresRepository: Stateful runtime layer with tenant-aware connection pooling
- PostgresRepository MAY use DatabaseManager utilities internally
"""

from loguru import logger
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from service.core.constants import get_tenant_schema_name


class DatabaseManager:
    """Handles database schema operations and connection management."""

    @staticmethod
    def sanitize_database_url(database_url: str) -> str:
        """Sanitize database URL to use postgresql:// instead of postgres://.

        Args:
            database_url: The database URL to sanitize

        Returns:
            Sanitized database URL
        """
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://")
        return database_url

    @staticmethod
    def create_engine_from_url(database_url: str, **engine_kwargs: object) -> Engine:
        """Create a SQLAlchemy engine with sanitized URL.

        Args:
            database_url: The database URL
            **engine_kwargs: Additional arguments to pass to create_engine

        Returns:
            SQLAlchemy Engine instance
        """
        sanitized_url = DatabaseManager.sanitize_database_url(database_url)
        return create_engine(sanitized_url, **engine_kwargs)

    @staticmethod
    def ensure_schema_exists(
        engine: Engine, tenant_id: str | None, commit: bool = True
    ) -> str:
        """Ensure the tenant schema exists in the database.

        Args:
            engine: SQLAlchemy engine to use for connection
            tenant_id: The tenant identifier, or None for default schema
            commit: Whether to commit the transaction (default: True)

        Returns:
            The schema name that was ensured to exist

        Raises:
            RuntimeError: If schema creation fails
        """
        schema_name = get_tenant_schema_name(tenant_id)

        # Skip creation for public schema (always exists)
        if schema_name == "public":
            logger.debug("Using default 'public' schema, no creation needed")
            return schema_name

        try:
            with engine.connect() as connection:
                # Use parameterized query with identifier quoting for security
                # PostgreSQL requires double quotes for identifiers
                connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                if commit:
                    connection.commit()

            logger.info(f"Schema '{schema_name}' is ready")
            return schema_name

        except SQLAlchemyError as e:
            logger.error(f"Failed to create schema '{schema_name}': {e}")
            raise RuntimeError(f"Database schema creation failed: {e}") from e

    @staticmethod
    def validate_schema_exists(engine: Engine, schema_name: str) -> bool:
        """Validate that a schema exists in the database.

        Args:
            engine: SQLAlchemy engine to use for connection
            schema_name: The schema name to validate

        Returns:
            True if schema exists, False otherwise
        """
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text(
                        "SELECT schema_name FROM information_schema.schemata "
                        "WHERE schema_name = :schema"
                    ),
                    {"schema": schema_name},
                )
                exists = result.fetchone() is not None
                if exists:
                    logger.debug(f"Schema '{schema_name}' exists")
                else:
                    logger.warning(f"Schema '{schema_name}' does not exist")
                return exists

        except SQLAlchemyError as e:
            logger.error(f"Failed to validate schema '{schema_name}': {e}")
            return False

    @staticmethod
    def test_connection(engine: Engine) -> bool:
        """Test database connection to ensure it's ready.

        Args:
            engine: SQLAlchemy engine to test

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.debug("Database connection test successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False
