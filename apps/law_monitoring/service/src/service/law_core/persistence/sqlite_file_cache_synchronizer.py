import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from loguru import logger

from service.law_core.background_work.workers_constants import (
    SYNC_BATCH_DELAY_SECONDS,
    SYNC_BATCH_SIZE,
)
from service.law_core.persistence.pharia_data_storage_backend import (
    PhariaDataStorageBackend,
)
from service.law_core.persistence.sqlite_file_cache import SqliteFileCache
from service.law_core.persistence.sqlite_file_cache_exclusion_policy import (
    SqliteFileCacheExclusionPolicy,
)


class SqliteFileCacheSynchronizer:
    """
    Handles background synchronization from PhariaData to SQLite cache.

    Features:
    - Parallel file fetching with configurable batch sizes
    - Progress tracking and error handling
    - Configurable "nice" mode for resource-friendly operation
    - Thread-safe status checking
    """

    def __init__(
        self,
        pharia_backend: PhariaDataStorageBackend,
        sqlite_cache: SqliteFileCache,
        exclusion_policy: SqliteFileCacheExclusionPolicy,
    ):
        """
        Initialize cache synchronizer.

        Args:
            pharia_backend: Source of truth storage backend
            sqlite_cache: Target cache for synchronization
            exclusion_policy: Policy to determine what should be cached
        """
        self._pharia = pharia_backend
        self._cache = sqlite_cache
        self._policy = exclusion_policy
        self._sync_thread: threading.Thread | None = None

    def start_sync(self, nice: bool = True) -> None:
        """
        Start background cache synchronization.

        Args:
            nice: If True, use smaller batches and delays to be resource-friendly
        """
        if self.is_running():
            logger.warning("Cache sync already running, skipping new sync")
            return

        logger.info("Starting background cache synchronization")
        self._sync_thread = threading.Thread(
            target=self._run_sync, args=(nice,), daemon=True, name="CacheSynchronizer"
        )
        self._sync_thread.start()

    def is_running(self) -> bool:
        """Check if synchronization is currently running."""
        return self._sync_thread is not None and self._sync_thread.is_alive()

    def _run_sync(self, nice: bool) -> None:
        """Main synchronization loop (runs in background thread)."""
        logger.info(f"Starting cache synchronization (nice={nice})")
        start_time = time.time()

        try:
            # Get all folders from PhariaData
            folders = self._pharia.list_folders()
            if not folders:
                logger.info("No folders found, sync complete")
                return

            # Filter cacheable folders
            cacheable_folders = [
                folder for folder in folders if self._policy.should_cache(folder)
            ]

            excluded_count = len(folders) - len(cacheable_folders)
            if excluded_count > 0:
                logger.info(f"Excluding {excluded_count} folders from cache")

            if not cacheable_folders:
                logger.info("No cacheable folders found, sync complete")
                return

            logger.info(f"Processing {len(cacheable_folders)} cacheable folders")

            # Collect all files to sync
            files_to_sync = self._collect_files_to_sync(cacheable_folders)

            if not files_to_sync:
                logger.info("No cacheable files found, sync complete")
                return

            logger.info(f"Found {len(files_to_sync)} files to synchronize")

            # Perform parallel synchronization
            self._sync_files_parallel(files_to_sync, nice)

            elapsed = time.time() - start_time
            logger.info(f"Cache synchronization completed in {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Cache synchronization failed after {elapsed:.2f}s: {e}")
            logger.warning("Continuing with partial cache")

    def _collect_files_to_sync(self, folders: List[str]) -> List[Tuple[str, str]]:
        """Collect all cacheable files from given folders."""
        files_to_sync = []
        total_discovered = 0

        for folder in folders:
            try:
                logger.debug(f"Discovering files in folder '{folder}'")
                filenames = self._pharia.list_files(folder)
                total_discovered += len(filenames)

                # Filter cacheable files
                cacheable_files = [
                    (folder, filename)
                    for filename in filenames
                    if self._policy.should_cache(folder, filename)
                ]

                files_to_sync.extend(cacheable_files)

            except Exception as e:
                logger.error(f"Failed to list files in folder '{folder}': {e}")
                continue

        logger.info(
            f"Collected {len(files_to_sync)}/{total_discovered} cacheable files"
        )
        return files_to_sync

    def _sync_files_parallel(
        self, files_to_sync: List[Tuple[str, str]], nice: bool
    ) -> None:
        """Synchronize files in parallel batches."""
        total_files = len(files_to_sync)
        successful = 0
        failed = 0

        # Configure batch processing
        if nice:
            batch_size = min(SYNC_BATCH_SIZE, total_files)
            batch_delay = SYNC_BATCH_DELAY_SECONDS
            max_workers = 1
        else:
            batch_size = min(50, total_files)
            batch_delay = 0
            max_workers = min(10, max(1, total_files // 20))

        logger.info(
            f"Batch config: size={batch_size}, workers={max_workers}, delay={batch_delay}s"
        )

        # Process in batches
        for batch_start in range(0, total_files, batch_size):
            batch_end = min(batch_start + batch_size, total_files)
            batch_files = files_to_sync[batch_start:batch_end]

            logger.debug(
                f"Processing batch {batch_start // batch_size + 1}: files {batch_start + 1}-{batch_end}"
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit batch tasks
                future_to_file = {
                    executor.submit(self._sync_single_file, folder, filename): (
                        folder,
                        filename,
                    )
                    for folder, filename in batch_files
                }

                # Process completed tasks
                for future in as_completed(future_to_file):
                    folder, filename = future_to_file[future]

                    try:
                        success = future.result()
                        if success:
                            successful += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error(
                            f"Unexpected error syncing '{folder}/{filename}': {e}"
                        )
                        failed += 1

            # Progress reporting
            progress_pct = (batch_end / total_files) * 100
            logger.info(
                f"Progress: {batch_end}/{total_files} ({progress_pct:.1f}%) - Success: {successful}, Failed: {failed}"
            )

            # Delay between batches if in nice mode
            if nice and batch_end < total_files:
                time.sleep(batch_delay)

        logger.info(f"Sync complete: {successful} successful, {failed} failed")

    def _sync_single_file(self, folder: str, filename: str) -> bool:
        """
        Synchronize a single file from PhariaData to cache.

        Returns:
            True if successful, False if failed
        """
        try:
            # Fetch from PhariaData
            content = self._pharia.load_file(folder, filename)

            if content is None:
                logger.warning(f"File '{folder}/{filename}' not found in PhariaData")
                return False

            # Save to cache
            self._cache.save_file(folder, filename, content)
            return True

        except Exception as e:
            logger.error(f"Failed to sync '{folder}/{filename}': {e}")
            return False
