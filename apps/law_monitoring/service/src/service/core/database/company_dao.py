from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from service.core.database.models import CompanyConfig, Team
from service.core.database.postgres_repository import PostgresRepository
from service.models import CompanyConfig as PydCompanyConfig


class CompanyDAO:
    """Data Access Object for company configuration and teams operations.

    This DAO provides simple CRUD accessors without enforcing any singleton
    semantics. Higher-level invariants (such as treating `CompanyConfig` as a
    singleton aggregate) must be enforced by the service layer.
    """

    def __init__(self, repo: PostgresRepository) -> None:
        self.repo = repo

    # Company config aggregate operations
    def get_or_create_default_company_config(
        self, default_config: PydCompanyConfig
    ) -> CompanyConfig:
        """Get the root aggregate (CompanyConfig with teams), creating from defaults if missing.

        Runs within a single transaction and returns the full aggregate eagerly loaded.
        """
        with self.repo.session_scope() as session:
            existing: Optional[CompanyConfig] = (
                session.query(CompanyConfig)
                .options(selectinload(CompanyConfig.teams))
                .first()
            )
            if existing is not None:
                return existing

            created = self._create_full_config_from_default(session, default_config)
            # Return a fully eager-loaded aggregate (config + teams)
            aggregate = (
                session.query(CompanyConfig)
                .options(selectinload(CompanyConfig.teams))
                .filter(CompanyConfig.id == created.id)
                .first()
            )
            assert aggregate is not None
            return aggregate

    # Private helpers
    def _create_full_config_from_default(
        self, session: Session, default_config: PydCompanyConfig
    ) -> CompanyConfig:
        config = CompanyConfig(company_description=default_config.company_description)
        session.add(config)
        session.flush()
        # Create teams
        for t in default_config.teams:
            team = Team(
                company_id=config.id,  # type: ignore[attr-defined]
                name=t.name,
                description=t.description,
                department=t.department,
                daily_processes=list(t.daily_processes),
                relevant_laws_or_topics=t.relevant_laws_or_topics,
            )
            session.add(team)
        session.flush()
        return config

    def update_company_description(
        self, company_id: int, description: Optional[str]
    ) -> CompanyConfig:
        """Update company description for a specific company id; raises if not found."""
        with self.repo.session_scope() as session:
            config = (
                session.query(CompanyConfig)
                .options(selectinload(CompanyConfig.teams))
                .filter(CompanyConfig.id == company_id)
                .first()
            )
            if config is None:
                raise ValueError("CompanyConfig not found for given id")
            config.company_description = description
            session.flush()
            session.refresh(config)
            return config

    # Team operations (scoped by company_id, no implicit company creation)
    def list_teams(self, company_id: int) -> List[Team]:
        """List all teams for a company."""
        with self.repo.session_scope() as session:
            return (
                session.query(Team)
                .filter(Team.company_id == company_id)
                .order_by(Team.name.asc())
                .all()
            )

    def get_team_by_name(self, company_id: int, team_name: str) -> Optional[Team]:
        """Get a team by case-insensitive name for a company."""
        normalized = team_name.strip().lower()
        if not normalized:
            return None
        with self.repo.session_scope() as session:
            return (
                session.query(Team)
                .filter(Team.company_id == company_id)
                .filter(func.lower(Team.name) == normalized)
                .first()
            )

    def upsert_team(
        self,
        *,
        company_id: int,
        name: str,
        description: str,
        department: str,
        daily_processes: List[str],
        relevant_laws_or_topics: str,
    ) -> Team:
        """Insert or update a team by name (case-insensitive) for a company."""
        with self.repo.session_scope() as session:
            existing: Optional[Team] = (
                session.query(Team)
                .filter(Team.company_id == company_id)
                .filter(func.lower(Team.name) == name.strip().lower())
                .first()
            )

            if existing is None:
                team = Team(
                    company_id=company_id,
                    name=name,
                    description=description,
                    department=department,
                    daily_processes=daily_processes,
                    relevant_laws_or_topics=relevant_laws_or_topics,
                )
                session.add(team)
                session.flush()
                session.refresh(team)
                return team
            else:
                existing.description = description
                existing.department = department
                existing.daily_processes = daily_processes
                existing.relevant_laws_or_topics = relevant_laws_or_topics
                session.flush()
                session.refresh(existing)
                return existing

    def delete_team_by_name(self, company_id: int, team_name: str) -> bool:
        """Delete a team by name (case-insensitive) for a company. Returns True if a row was deleted."""
        normalized = team_name.strip().lower()
        if not normalized:
            return False
        with self.repo.session_scope() as session:
            existing: Optional[Team] = (
                session.query(Team)
                .filter(Team.company_id == company_id)
                .filter(func.lower(Team.name) == normalized)
                .first()
            )
            if existing is None:
                return False
            session.delete(existing)
            # commit happens in session_scope
            return True
