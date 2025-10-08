import threading
from typing import List, Optional, Union

from loguru import logger

from service.core.utils.singleton import SingletonMeta
from service.core.utils.utils import thread_safe
from service.dependencies import with_settings
from service.law_core.persistence.pharia_data_storage_backend import (
    pharia_data_storage_backend,
)
from service.law_core.persistence.sqlite_file_cache import sqlite_file_cache
from service.law_core.persistence.sqlite_file_cache_exclusion_policy import (
    SqliteFileCacheExclusionPolicy,
)
from service.law_core.persistence.sqlite_file_cache_synchronizer import (
    SqliteFileCacheSynchronizer,
)
from service.law_core.persistence.storage_backend import (
    StorageBackend,
    StorageBackendType,
)


class PhariaDataSyncedSqliteStorageBackend(StorageBackend, metaclass=SingletonMeta):
    """
    Hybrid storage backend that combines SQLite caching with PhariaData as source of truth.

    Features:
    - Fast reads from SQLite cache
    - All writes go to PhariaData (authoritative)
    - Configurable folder/file patterns to exclude from caching
    - Thread-safe operations
    - Disk-based SQLite database for performance
    - Background cache initialization

    Read Strategy:
    - Check if folder/file should be cached
    - If cached: read from SQLite
    - If not cached: read directly from PhariaData

    Write Strategy:
    - Always write to PhariaData first (source of truth)
    - If cacheable: update SQLite cache
    - If not cacheable: PhariaData only
    """

    def __init__(self) -> None:
        """
        Initialize the hybrid storage backend.

        Creates PhariaData backend instance, SQLite database,
        and sets up exclusion patterns for non-cacheable data.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        # Initialize PhariaData backend (source of truth)
        self._pharia_backend = pharia_data_storage_backend

        # Thread safety lock - use RLock to allow recursive locking within same thread
        self._lock = threading.RLock()

        self._sqlite_cache = sqlite_file_cache

        self._exclusion_policy = SqliteFileCacheExclusionPolicy()

        self._cache_synchronizer = SqliteFileCacheSynchronizer(
            self._pharia_backend, self._sqlite_cache, self._exclusion_policy
        )

        settings = with_settings()
        if settings.storage_type == StorageBackendType.PHARIA_DATA_SYNCED_SQLITE.value:
            self._cache_synchronizer.start_sync(nice=False)

        self._initialized = True

        logger.info("PhariaDataSyncedSqliteStorageBackend initialized successfully")

    @thread_safe
    def save_file(self, folder: str, filename: str, content: Union[str, bytes]) -> str:
        """
        Save content to storage (PhariaData as source of truth, SQLite as cache).

        Args:
            folder: Folder where to save the file
            filename: Name of the file (without path)
            content: Content to save (string for text files, bytes for binary files)

        Returns:
            Backend-specific identifier where the file was saved
        """

        try:
            # Always write to PhariaData first (source of truth)
            pharia_file_id = self._pharia_backend.save_file(folder, filename, content)

            # Update SQLite cache if this file should be cached
            if self._exclusion_policy.should_cache(folder, filename):
                try:
                    self._sqlite_cache.save_file(folder, filename, content)
                except Exception as e:
                    logger.warning(
                        f"SQLite cache update failed for '{folder}/{filename}': {e}"
                    )

            return pharia_file_id

        except Exception as e:
            logger.error(f"Failed to save file '{filename}' to folder '{folder}': {e}")
            raise

    @thread_safe
    def load_file(self, folder: str, filename: str) -> Optional[Union[str, bytes]]:
        """
        Load content from storage (SQLite cache if available, otherwise PhariaData).

        Args:
            folder: Folder containing the file
            filename: Name of the file (without path)

        Returns:
            File content if exists (str or bytes depending on original type), None otherwise
        """

        try:
            # Check if this file should be cached
            if self._exclusion_policy.should_cache(folder, filename):
                # Try to read from SQLite cache first
                cached_content = self._sqlite_cache.get_file(folder, filename)
                if cached_content is not None:
                    return cached_content

                # Not in cache - read from PhariaData and cache it
                content = self._pharia_backend.load_file(folder, filename)

                if content is not None:
                    # Cache the file for future reads (on-demand caching)
                    try:
                        self._sqlite_cache.save_file(folder, filename, content)
                    except Exception as e:
                        logger.warning(
                            f"Failed to cache '{folder}/{filename}' after fetch: {e}"
                        )

                return content
            else:
                # Excluded from cache - read directly from PhariaData
                return self._pharia_backend.load_file(folder, filename)

        except Exception as e:
            logger.error(
                f"Failed to load file '{filename}' from folder '{folder}': {e}"
            )
            return None

    @thread_safe
    def file_exists(self, folder: str, filename: str) -> bool:
        """
        Check if a file exists in storage.

        Optimized to check SQLite cache first for cacheable files, then PhariaData.
        If found in PhariaData, automatically caches the file content.

        Args:
            folder: Folder to check
            filename: Name of the file (without path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Check if this file should be cached
            if self._exclusion_policy.should_cache(folder, filename):
                # First check SQLite cache
                cached_content = self._sqlite_cache.get_file(folder, filename)
                if cached_content is not None:
                    return True

                exists_in_pharia = self._pharia_backend.file_exists(folder, filename)

                if exists_in_pharia:
                    # File exists in PhariaData - cache it immediately for future reads
                    try:
                        content = self._pharia_backend.load_file(folder, filename)

                        if content is not None:
                            self._sqlite_cache.save_file(folder, filename, content)
                        else:
                            logger.warning(
                                f"File '{folder}/{filename}' exists in PhariaData but content is None"
                            )

                    except Exception as e:
                        logger.warning(
                            f"Failed to cache '{folder}/{filename}' during file_exists: {e}"
                        )
                        # Continue - existence check succeeded even if caching failed

                return exists_in_pharia
            else:
                # File not cacheable - check PhariaData directly (authoritative)
                return self._pharia_backend.file_exists(folder, filename)

        except Exception as e:
            logger.error(
                f"Error checking if file '{filename}' exists in folder '{folder}': {e}"
            )
            return False

    @thread_safe
    def list_files(self, folder: str, pattern: Optional[str] = None) -> List[str]:
        """
        List files in a storage folder.

        Args:
            folder: Folder to list files from
            pattern: Optional glob pattern to filter files

        Returns:
            List of filenames (without folder path)
        """
        try:
            # Always use PhariaData for listing (authoritative)
            return self._pharia_backend.list_files(folder, pattern)

        except Exception as e:
            logger.error(f"Error listing files in folder '{folder}': {e}")
            return []

    @thread_safe
    def delete_file(self, folder: str, filename: str) -> bool:
        """
        Delete a file from storage.

        Args:
            folder: Folder containing the file
            filename: Name of the file (without path)

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Delete from PhariaData first (source of truth)
            success = self._pharia_backend.delete_file(folder, filename)

            if success and self._exclusion_policy.should_cache(folder, filename):
                # Remove from SQLite cache
                try:
                    self._sqlite_cache.delete_file(folder, filename)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove '{folder}/{filename}' from SQLite cache: {e}"
                    )

            return success

        except Exception as e:
            logger.error(
                f"Error deleting file '{filename}' from folder '{folder}': {e}"
            )
            return False

    @thread_safe
    def list_folders(self) -> List[str]:
        """
        List all folders in the storage backend.

        Returns:
            List of folder names
        """
        try:
            return self._pharia_backend.list_folders()
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            return []

    @thread_safe
    def create_folder(self, folder: str) -> bool:
        """
        Create a new folder in the storage backend.

        Args:
            folder: Name of the folder to create

        Returns:
            True if folder was created or already exists, False on failure
        """
        try:
            return self._pharia_backend.create_folder(folder)

        except Exception as e:
            logger.error(f"Error creating folder '{folder}': {e}")
            return False

    @thread_safe
    def get_files_in_folder(self, folder: str) -> List[str]:
        """
        Get all files in a specific folder.

        Args:
            folder: Folder to get files from

        Returns:
            List of filenames (without folder path)
        """
        try:
            return self._pharia_backend.get_files_in_folder(folder)

        except Exception as e:
            logger.error(f"Error getting files in folder '{folder}': {e}")
            return []

    @thread_safe
    def clear_cache(self) -> bool:
        """
        Clear the entire SQLite cache database.

        This removes all cached files but does not affect the PhariaData backend
        (which remains the source of truth).

        Returns:
            True if cache was cleared successfully, False otherwise
        """
        return self._sqlite_cache.clear()

    @thread_safe
    def clear_and_reinitialize_cache(self) -> bool:
        """
        Clear the SQLite cache and reinitialize it from PhariaData.

        This is a comprehensive cache refresh that:
        1. Clears all cached data
        2. Performs bulk synchronization from PhariaData in a background thread

        Returns:
            True if clear and reinitialize was successful, False otherwise
        """
        try:
            logger.info("Starting cache clear and reinitialize")

            if not self.clear_cache():
                logger.error("Failed to clear cache")
                return False

            logger.info("Starting background reinitialize")
            self._cache_synchronizer.start_sync(nice=True)

            logger.info("Cache clear and reinitialize initiated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to clear and reinitialize cache: {e}")
            return False

    def is_cache_initialization_running(self) -> bool:
        """Check if cache initialization is running."""
        return self._cache_synchronizer.is_running()


# Singleton instance - will be imported by storage factory
pharia_data_synced_sqlite_storage_backend = PhariaDataSyncedSqliteStorageBackend()
