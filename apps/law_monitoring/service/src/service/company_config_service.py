"""
DB-backed company configuration service for managing company description and team data.

This service persists and retrieves the company description and teams
from PostgreSQL via SQLAlchemy. On first access, if no configuration is
present in the DB, it persists the default configuration (including teams).
"""

from loguru import logger

from service.core.database.company_dao import CompanyDAO
from service.core.database.models import CompanyConfig as ORMCompanyConfig
from service.core.database.models import Team as ORMTeam
from service.core.database.postgres_repository import create_postgres_repository
from service.core.utils.singleton import SingletonMeta
from service.dependencies import with_settings
from service.law_core.defaults.default_company_config import get_default_company_config
from service.models import CompanyConfig, TeamDescription


class CompanyConfigService(metaclass=SingletonMeta):
    """Service for managing company configuration as a root aggregate.

    Responsibilities:
    - Enforce singleton invariant for `CompanyConfig` at the service layer
    - Always operate on the full aggregate (company config with teams)
    - On reads: always fetch `CompanyConfig` with teams from the DB
    - On writes: ensure the singleton exists, then persist changes and return
      a view backed by a fresh aggregate read
    """

    def __init__(self) -> None:
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        settings = with_settings()
        repo = create_postgres_repository(settings)
        self.dao = CompanyDAO(repo)

        self._initialized = True

    def get_department_teams_mapping(self, department: str) -> set[str]:
        """
        Get the mapping of department to team names with caching.

        Args:
            department: Department name to get teams for

        Returns:
            Set of lowercase team names that belong to the department
        """
        config = self.get_company_config()
        department_teams = set()
        department_lower = department.lower().strip()

        for team in config.teams:
            if team.department and team.department.strip().lower() == department_lower:
                department_teams.add(team.name.lower().strip())

        logger.debug(
            f"Department '{department}' mapped to {len(department_teams)} teams: {department_teams}"
        )
        return department_teams

    def get_company_config(self) -> CompanyConfig:
        """
        Get the current company config aggregate (with teams), creating from
        defaults if missing (enforced in DAO in a single transaction).

        Returns:
            CompanyConfig object
        """
        orm_config = self.dao.get_or_create_default_company_config(
            get_default_company_config()
        )
        return self._to_pydantic_config(orm_config)

    def get_company_description(self) -> str | None:
        """
        Get the current company description.

        Returns:
            Company description string, or None if not set
        """
        try:
            return self.get_company_config().company_description
        except Exception as e:
            logger.error(f"Error getting company description: {e}")
            return None

    def get_all_teams(self) -> list[TeamDescription]:
        """
        Get all team descriptions.

        Returns:
            List of TeamDescription objects
        """
        try:
            return self.get_company_config().teams
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []

    def add_or_update_company_description(self, description: str) -> str:
        """
        Add or update the company description.

        Args:
            description: New company description text

        Returns:
            The saved company description
        """

        description = description.strip()
        if not description:
            raise ValueError("Company description cannot be empty")

        try:
            # Ensure aggregate exists and get id
            orm_config = self.dao.get_or_create_default_company_config(
                get_default_company_config()
            )
            if orm_config is None:
                raise RuntimeError("Company configuration was not initialized")
            updated = self.dao.update_company_description(orm_config.id, description)
            logger.info("Successfully updated company description (DB)")
            return updated.company_description or ""
        except Exception as e:
            logger.error(f"Error updating company description: {e}")
            raise RuntimeError(f"Failed to update company description: {e}") from e

    def add_or_update_team(self, team: TeamDescription) -> TeamDescription:
        """
        Add or update a team description. Teams are identified by name (case-insensitive).

        Args:
            team: TeamDescription object to add or update

        Returns:
            The saved TeamDescription object
        """
        team_name_lower = team.name.strip().lower()

        if not team_name_lower:
            raise ValueError("Team name cannot be empty")

        try:
            # Ensure config exists and fetch ORM for company_id (full aggregate)
            orm_config = self.dao.get_or_create_default_company_config(
                get_default_company_config()
            )
            if orm_config is None:
                raise RuntimeError("Company configuration was not initialized")

            saved = self.dao.upsert_team(
                company_id=orm_config.id,
                name=team.name.strip(),
                description=team.description,
                department=team.department,
                daily_processes=list(team.daily_processes),
                relevant_laws_or_topics=team.relevant_laws_or_topics,
            )
            return self._to_pydantic_team(saved)
        except Exception as e:
            logger.error(f"Error updating team '{team.name}': {e}")
            raise RuntimeError(f"Failed to update team '{team.name}': {e}") from e

    def get_team_by_name(self, team_name: str) -> TeamDescription | None:
        """
        Get a specific team by name (case-insensitive).

        Args:
            team_name: Name of the team to retrieve
        """
        team_name_lower = team_name.strip().lower()
        if not team_name_lower:
            return None

        try:
            orm_config = self.dao.get_or_create_default_company_config(
                get_default_company_config()
            )
            if orm_config is None:
                return None
            team = self.dao.get_team_by_name(orm_config.id, team_name)
            return self._to_pydantic_team(team) if team else None
        except Exception as e:
            logger.error(f"Error getting team '{team_name}': {e}")
            return None

    def delete_team(self, team_name: str) -> bool:
        """
        Delete a team by name (case-insensitive).

        Args:
            team_name: Name of the team to delete

        Returns:
            True if team was deleted, False if team was not found
        """
        if not team_name or not team_name.strip():
            return False

        try:
            orm_config = self.dao.get_or_create_default_company_config(
                get_default_company_config()
            )
            if orm_config is None:
                return False
            return self.dao.delete_team_by_name(orm_config.id, team_name)
        except Exception as e:
            logger.error(f"Error deleting team '{team_name}': {e}")
            raise RuntimeError(f"Failed to delete team '{team_name}': {e}") from e

    @staticmethod
    def _to_pydantic_team(team: ORMTeam) -> TeamDescription:
        return TeamDescription(
            name=team.name,
            description=team.description,
            department=team.department,
            daily_processes=list(team.daily_processes or []),
            relevant_laws_or_topics=team.relevant_laws_or_topics,
        )

    @staticmethod
    def _to_pydantic_config(cfg: ORMCompanyConfig) -> CompanyConfig:
        teams: list[TeamDescription] = [
            CompanyConfigService._to_pydantic_team(t) for t in (cfg.teams or [])
        ]
        return CompanyConfig(company_description=cfg.company_description, teams=teams)


company_config_service = CompanyConfigService()
