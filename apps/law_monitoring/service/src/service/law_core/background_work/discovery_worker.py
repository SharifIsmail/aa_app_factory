import json
from datetime import datetime, timedelta

from loguru import logger

from service.core.database.laws_dao import LawsDAO
from service.core.database.model_adapters import legalact_to_law
from service.core.database.postgres_repository import create_postgres_repository
from service.core.utils.utils import generate_url_hash
from service.dependencies import with_settings
from service.law_core.background_work.base_worker import BaseWorker
from service.law_core.background_work.workers_constants import (
    DATA_FOLDER,
    DISCOVERY_DATA_FILE,
    DISCOVERY_FIRST_RUN_LOOKBACK_HOURS,
    DISCOVERY_SAFETY_MARGIN_MINUTES,
)
from service.law_core.eur_lex_service import eur_lex_service
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.metrics import (
    discovery_laws_failed,
    discovery_laws_found,
    discovery_laws_saved,
    discovery_laws_skipped,
)
from service.models import LegalAct


class DiscoveryWorker(BaseWorker):
    """Worker for discovering and storing new legal acts from EUR-Lex."""

    def __init__(self) -> None:
        """Initialize the discovery worker."""
        # Initialize database components
        settings = with_settings()
        self.postgres_repo = create_postgres_repository(settings)
        self.laws_dao = LawsDAO(self.postgres_repo)

        # Keep storage backend only for discovery data file
        self.storage_backend = get_configured_storage_backend()

        super().__init__("discovery")

    def _do_work(self) -> dict:
        """
        Perform the discovery work.

        Returns:
            Dictionary with discovery results
        """
        # Load previous discovery data
        discovery_data = self._load_discovery_data()

        # Calculate search date range
        search_start_date, search_end_date = self._calculate_search_range(
            discovery_data
        )

        logger.info(
            f"Discovery worker: searching for laws from {search_start_date} to {search_end_date}"
        )

        # Fetch legal acts from EUR-Lex
        legal_acts_response = eur_lex_service.get_legal_acts_by_date_range(
            search_start_date, search_end_date
        )

        # Process and save each legal act
        successful_saves = 0
        failed_saves = 0
        skipped_existing = 0
        discovered_laws = []
        errors = []

        # Update discovery metrics
        discovery_laws_found.inc(len(legal_acts_response.legal_acts))

        for legal_act in legal_acts_response.legal_acts:
            try:
                file_id, was_newly_saved = self._save_legal_act(
                    legal_act, datetime.now()
                )
                discovered_laws.append(file_id)
                if was_newly_saved:
                    successful_saves += 1
                    discovery_laws_saved.inc()
                    logger.debug(f"Discovery worker: saved legal act {file_id}")
                else:
                    skipped_existing += 1
                    discovery_laws_skipped.inc()
                    logger.debug(f"Discovery worker: skipped existing law {file_id}")
            except Exception as e:
                failed_saves += 1
                discovery_laws_failed.inc()
                error_msg = f"Failed to save legal act '{legal_act.title}': {str(e)}"
                errors.append(error_msg)
                logger.error(f"Discovery worker: {error_msg}")

        # Update discovery data
        discovery_data["last_run_at"] = datetime.now().isoformat()
        if failed_saves == 0:
            discovery_data["last_successful_run_at"] = datetime.now().isoformat()
        discovery_data["total_laws_discovered"] = (
            discovery_data.get("total_laws_discovered", 0) + successful_saves
        )
        discovery_data["total_discovery_runs"] = (
            discovery_data.get("total_discovery_runs", 0) + 1
        )

        if discovery_data.get("first_discovery_run") is None:
            discovery_data["first_discovery_run"] = datetime.now().isoformat()

        self._save_discovery_data(discovery_data)

        # Return results for run record
        return {
            "total_laws_found": len(legal_acts_response.legal_acts),
            "successful_saves": successful_saves,
            "skipped_existing": skipped_existing,
            "failed_saves": failed_saves,
            "discovered_laws": discovered_laws,
            "errors": errors,
        }

    def _calculate_search_range(
        self, discovery_data: dict
    ) -> tuple[datetime, datetime]:
        """
        Calculate the date range for searching new legal acts.

        Args:
            discovery_data: Discovery data dictionary

        Returns:
            Tuple of (start_date, end_date) for the search
        """
        end_date = datetime.now()

        if discovery_data.get("last_successful_run_at"):
            # Start from last successful run minus safety margin
            last_run = datetime.fromisoformat(discovery_data["last_successful_run_at"])
            start_date = last_run - timedelta(minutes=DISCOVERY_SAFETY_MARGIN_MINUTES)
        else:
            # First run, no previous successful run
            start_date = end_date - timedelta(hours=DISCOVERY_FIRST_RUN_LOOKBACK_HOURS)

        return start_date, end_date

    def _save_legal_act(
        self, legal_act: LegalAct, discovered_at: datetime
    ) -> tuple[str, bool]:
        """
        Save a legal act to database.

        Args:
            legal_act: The legal act to save
            discovered_at: When this law was discovered

        Returns:
            Tuple of (file_id, was_newly_saved)
        """
        file_id = generate_url_hash(legal_act.expression_url)

        # Check if law already exists in database
        if self.laws_dao.exists(file_id):
            logger.debug(
                f"Discovery worker: Law with expression_url {legal_act.expression_url} already exists with file_id {file_id}"
            )
            return file_id, False

        # Convert LegalAct to Law ORM model
        law = legalact_to_law(legal_act, discovered_at=discovered_at, law_id=file_id)

        # Save to database
        self.laws_dao.upsert(law)

        return file_id, True

    def _load_discovery_data(self) -> dict:
        """
        Load the discovery data from storage.

        Returns:
            Dictionary with discovery data (creates default if doesn't exist)
        """
        content = self.storage_backend.load_file(DATA_FOLDER, DISCOVERY_DATA_FILE)
        if content:
            try:
                return json.loads(content)
            except Exception as e:
                logger.warning(f"Discovery worker: failed to parse discovery data: {e}")

        # Return default data
        return {
            "last_run_at": None,
            "last_successful_run_at": None,
            "total_laws_discovered": 0,
            "total_discovery_runs": 0,
            "first_discovery_run": None,
        }

    def _save_discovery_data(self, data: dict) -> None:
        """
        Save discovery data to storage.

        Args:
            data: The discovery data dictionary to save
        """
        content = json.dumps(data, indent=2)
        self.storage_backend.save_file(DATA_FOLDER, DISCOVERY_DATA_FILE, content)

    def get_discovery_data(self) -> dict:
        """Get the current discovery data."""
        return self._load_discovery_data()

    def list_discovered_laws(self) -> list[str]:
        """List all discovered law file IDs."""
        from service.models import LawStatus

        # Get all RAW laws from database
        raw_laws = self.laws_dao.list_by_status(LawStatus.RAW, limit=10000)
        return [law.law_id for law in raw_laws]
