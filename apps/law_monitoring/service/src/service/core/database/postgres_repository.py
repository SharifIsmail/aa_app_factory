"""PostgreSQL repository for runtime database access and session management.

LAYER: Application Runtime / Data Access Layer
==============================================

This module provides the STATEFUL, APPLICATION-RUNTIME layer for database
operations. It manages the SQLAlchemy engine, connection pooling, session
lifecycle, and tenant-aware query execution throughout the application's lifetime.

When to use PostgresRepository:
- Runtime query execution in API endpoints
- Transaction management across multiple operations
- Session-based ORM operations
- Background tasks that need database access
- Any business logic requiring database queries

When NOT to use PostgresRepository:
- One-time schema creation (use DatabaseManager instead)
- Migration setup (use DatabaseManager instead)
- Simple URL sanitization (use DatabaseManager instead)

Key Features:
1. **Tenant-Aware Connection Pooling**: Automatically sets search_path to the
   correct tenant schema on every connection checkout via SQLAlchemy event listener
2. **Session Management**: Provides `session_scope()` context manager for
   transactional operations
3. **Retry Logic**: Exponential backoff retry mechanism for database initialization
4. **FastAPI Integration**: Dependency injection via `create_postgres_repository()`

Relationship to DatabaseManager:
- PostgresRepository: Stateful runtime layer (lives entire app lifetime)
- DatabaseManager: Stateless utilities for infrastructure setup
- PostgresRepository uses DatabaseManager for low-level operations

Example Usage:
    # In FastAPI endpoint
    @app.get("/items")
    def get_items(repo: PostgresRepository = Depends(create_postgres_repository)):
        with repo.session_scope() as session:
            items = session.query(Item).all()
            return items

    # In background task
    repo = create_postgres_repository(settings)
    with repo.session_scope() as session:
        # Multi-step transaction with automatic rollback on error
        session.add(new_item)
        session.flush()
        session.add(related_record)
"""

import time
from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated, Iterator

from fastapi import Depends, HTTPException
from loguru import logger
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from service.core.constants import get_tenant_schema_name
from service.core.database.database_manager import DatabaseManager
from service.dependencies import with_settings
from service.settings import Settings


class PostgresRepository:
    def __init__(
        self,
        database_url: str,
        tenant_id: str | None = None,
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ) -> None:
        """Initialize database engine and session factory."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        try:
            self.engine = DatabaseManager.create_engine_from_url(
                database_url=database_url,
                pool_pre_ping=True,
            )

            # Determine the schema name using centralized function
            schema_name = get_tenant_schema_name(tenant_id)

            @event.listens_for(self.engine, "checkout")
            def set_schema(dbapi_connection, connection_record, connection_proxy):  # type: ignore
                """Set the search_path for every connection checkout."""
                cursor = dbapi_connection.cursor()
                # Use proper identifier quoting to prevent SQL injection
                # PostgreSQL identifier quoting with double quotes
                quoted_schema = f'"{schema_name}"'
                cursor.execute(f"SET search_path TO {quoted_schema}")
                cursor.close()

            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
            )

            self._initialize_database_with_retry()

            logger.info("PostgreSQL engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL engine: {e}")
            raise HTTPException(
                status_code=500, detail="Database initialization failed."
            ) from e

    def _initialize_database_with_retry(self) -> None:
        """Initialize database with retry logic."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Database initialization attempt {attempt}/{self.max_retries}"
                )
                self._wait_for_database_ready()
                logger.info("Database initialized successfully")
                return
            except OperationalError as e:
                logger.warning(
                    f"Database not ready (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries:
                    logger.error("Max retries reached. Database initialization failed.")
                    raise
                time.sleep(self.retry_delay * attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error during database initialization: {e}")
                raise

    def _wait_for_database_ready(self) -> None:
        """Test database connection to ensure it's ready."""
        DatabaseManager.test_connection(self.engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Provide a transactional scope around a series of operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


@lru_cache(maxsize=1)
def create_postgres_repository(
    settings: Annotated[Settings, Depends(with_settings)],
) -> PostgresRepository:
    db_url = str(settings.database_url.get_secret_value())
    return PostgresRepository(database_url=db_url, tenant_id=settings.tenant_id)
