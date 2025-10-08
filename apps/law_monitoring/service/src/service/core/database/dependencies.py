"""Database dependency injection functions."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from service.core.database.company_dao import CompanyDAO
from service.core.database.laws_dao import LawsDAO
from service.core.database.postgres_repository import (
    PostgresRepository,
    create_postgres_repository,
)
from service.dependencies import with_settings
from service.settings import Settings


@lru_cache(maxsize=1)
def get_postgres_repository(
    settings: Annotated[Settings, Depends(with_settings)],
) -> PostgresRepository:
    """Get PostgreSQL repository instance."""
    return create_postgres_repository(settings)


def get_laws_dao(
    postgres_repo: Annotated[PostgresRepository, Depends(get_postgres_repository)],
) -> LawsDAO:
    """Get Laws DAO instance."""
    return LawsDAO(postgres_repo)


def get_company_dao(
    postgres_repo: Annotated[PostgresRepository, Depends(get_postgres_repository)],
) -> CompanyDAO:
    """Get Company DAO instance."""
    return CompanyDAO(postgres_repo)
