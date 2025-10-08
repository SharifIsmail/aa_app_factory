import json
from datetime import datetime
from typing import Dict

from loguru import logger

from service.law_core.background_work.base_worker import BaseWorker
from service.law_core.background_work.workers_constants import (
    DATA_FOLDER,
    DATABASE_SYNC_DATA_FILE,
    DATABASE_SYNC_WORKER_TIMEOUT_HOURS,
)
from service.law_core.persistence.pharia_data_synced_sqlite_storage_backend import (
    PhariaDataSyncedSqliteStorageBackend,
)
from service.law_core.persistence.storage_factory import get_configured_storage_backend


class DatabaseSyncWorker(BaseWorker):
    """Worker for synchronizing SQLite cache with PhariaData."""

    RUN_TIMEOUT_MINUTES = DATABASE_SYNC_WORKER_TIMEOUT_HOURS * 60

    def __init__(self) -> None:
        """Initialize the database sync worker."""
        self.storage_backend = get_configured_storage_backend()
        super().__init__("database_sync")
        if not isinstance(self.storage_backend, PhariaDataSyncedSqliteStorageBackend):
            raise RuntimeError(
                f"Invalid storage backend: {self.storage_backend}, only PhariaDataSyncedSqliteStorageBackend is supported for DatabaseSyncWorker."
            )

    def _do_work(self) -> Dict:
        """
        Perform the database synchronization work.
        Simply calls clear_and_reinitialize_cache() on the storage backend.

        Returns:
            Dictionary with sync results and statistics
        """
        logger.info("DatabaseSyncWorker: starting cache synchronization")
        start_time = datetime.now()

        # Load sync metadata
        sync_data = self._load_sync_data()

        try:
            # Perform cache clear and reinitialize (runs in background thread)
            success = self.storage_backend.clear_and_reinitialize_cache()  # type: ignore

            # Calculate duration
            duration_seconds = (datetime.now() - start_time).total_seconds()

            if success:
                # Update sync metadata on success
                sync_data["last_sync_at"] = start_time.isoformat()
                sync_data["last_successful_sync_at"] = start_time.isoformat()
                sync_data["total_syncs_performed"] = (
                    sync_data.get("total_syncs_performed", 0) + 1
                )
                sync_data["total_successful_syncs"] = (
                    sync_data.get("total_successful_syncs", 0) + 1
                )

                self._save_sync_data(sync_data)

                sync_results = {
                    "sync_type": "clear_and_reinitialize",
                    "success": True,
                    "sync_duration_seconds": duration_seconds,
                    "cache_initialization_started": True,
                    "errors": 0,
                    "error_details": [],
                }

                logger.info(
                    f"DatabaseSyncWorker: cache synchronization initiated successfully in {duration_seconds:.1f}s"
                )
                return sync_results
            else:
                # Handle failure
                sync_data["last_sync_at"] = start_time.isoformat()
                sync_data["total_syncs_performed"] = (
                    sync_data.get("total_syncs_performed", 0) + 1
                )
                sync_data["total_failed_syncs"] = (
                    sync_data.get("total_failed_syncs", 0) + 1
                )

                self._save_sync_data(sync_data)

                error_result = {
                    "sync_type": "clear_and_reinitialize",
                    "success": False,
                    "sync_duration_seconds": duration_seconds,
                    "cache_initialization_started": False,
                    "errors": 1,
                    "error_details": [
                        "Failed to initiate cache clear and reinitialize"
                    ],
                }

                logger.error(
                    f"DatabaseSyncWorker: cache synchronization failed in {duration_seconds:.1f}s"
                )
                return error_result

        except Exception as e:
            # Update sync metadata on exception
            sync_data["last_sync_at"] = start_time.isoformat()
            sync_data["total_syncs_performed"] = (
                sync_data.get("total_syncs_performed", 0) + 1
            )
            sync_data["total_failed_syncs"] = sync_data.get("total_failed_syncs", 0) + 1
            self._save_sync_data(sync_data)

            duration_seconds = (datetime.now() - start_time).total_seconds()
            error_result = {
                "sync_type": "clear_and_reinitialize",
                "success": False,
                "sync_duration_seconds": duration_seconds,
                "cache_initialization_started": False,
                "errors": 1,
                "error_details": [str(e)],
            }

            logger.error(
                f"DatabaseSyncWorker: sync failed with exception after {duration_seconds:.1f}s: {e}"
            )
            return error_result

    def _load_sync_data(self) -> Dict:
        """
        Load sync metadata from storage.

        Returns:
            Dictionary with sync metadata (creates default if doesn't exist)
        """
        content = self.storage_backend.load_file(DATA_FOLDER, DATABASE_SYNC_DATA_FILE)
        if content:
            try:
                return json.loads(content)
            except Exception as e:
                logger.warning(f"DatabaseSyncWorker: failed to parse sync data: {e}")

        # Return default sync data
        return {
            "last_sync_at": None,
            "last_successful_sync_at": None,
            "total_syncs_performed": 0,
            "total_successful_syncs": 0,
            "total_failed_syncs": 0,
            "first_sync_run": None,
        }

    def _save_sync_data(self, data: Dict) -> None:
        """
        Save sync metadata to storage.

        Args:
            data: The sync data dictionary to save
        """
        # Set first run timestamp if not already set
        if data.get("first_sync_run") is None:
            data["first_sync_run"] = datetime.now().isoformat()

        content = json.dumps(data, indent=2)
        self.storage_backend.save_file(DATA_FOLDER, DATABASE_SYNC_DATA_FILE, content)

    def get_sync_data(self) -> Dict:
        """Get the current sync data."""
        return self._load_sync_data()

    def get_sync_statistics(self) -> Dict:
        """
        Get comprehensive sync statistics.

        Returns:
            Dictionary with sync statistics and health metrics
        """
        sync_data = self._load_sync_data()

        # Calculate time since last sync
        last_sync = sync_data.get("last_sync_at")
        last_successful_sync = sync_data.get("last_successful_sync_at")

        time_since_last_sync = None
        time_since_successful_sync = None

        if last_sync:
            time_since_last_sync = (
                datetime.now() - datetime.fromisoformat(last_sync)
            ).total_seconds()

        if last_successful_sync:
            time_since_successful_sync = (
                datetime.now() - datetime.fromisoformat(last_successful_sync)
            ).total_seconds()

        # Consider sync healthy if it ran successfully within the last 26 hours (24h interval + 2h grace period)
        is_healthy = (
            time_since_successful_sync is not None
            and time_since_successful_sync < 26 * 3600  # 26 hours in seconds
        )

        # Check if cache initialization is currently running
        cache_init_running = False
        try:
            cache_init_running = self.storage_backend.is_cache_initialization_running()  # type: ignore
        except Exception as e:
            logger.warning(
                f"DatabaseSyncWorker: failed to check cache initialization status: {e}"
            )

        return {
            "sync_data": sync_data,
            "time_since_last_sync_seconds": time_since_last_sync,
            "time_since_successful_sync_seconds": time_since_successful_sync,
            "sync_health": "healthy" if is_healthy else "unhealthy",
            "sync_schedule": "daily_at_3am_utc",
            "cache_initialization_running": cache_init_running,
        }
