import os
import tempfile
from typing import Any, Optional

import diskcache as dc

from service.core.utils.singleton import SingletonMeta


class CacheService(metaclass=SingletonMeta):
    """
    Service responsible for temporary data caching operations.

    This class uses the SingletonMeta metaclass to ensure only one instance exists.
    Uses diskcache for robust, thread-safe disk-based caching.
    """

    def __init__(self) -> None:
        """Initialize the CacheService singleton."""
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        # Initialize diskcache with temporary directory
        temp_dir = tempfile.gettempdir()
        cache_dir = os.path.join(temp_dir, "law_monitoring_cache")

        # Create diskcache instance
        self.cache = dc.Cache(cache_dir)

        # Mark as initialized
        self._initialized = True

    def load_from_cache(self, cache_id: str) -> Optional[Any]:
        """
        Load data from cache using the given cache ID.

        Args:
            cache_id: The identifier for the cached data

        Returns:
            The cached data if it exists, None otherwise
        """
        return self.cache.get(cache_id)

    def save_to_cache(self, cache_id: str, data: Any) -> str:
        """
        Save data to cache with the given cache ID.

        Args:
            cache_id: The identifier for the cached data
            data: The data to cache

        Returns:
            A confirmation string indicating the data was cached
        """
        self.cache[cache_id] = data
        return f"cached:{cache_id}"

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached items."""
        return len(self.cache)

    def delete_from_cache(self, cache_id: str) -> bool:
        """
        Delete a specific item from cache.

        Args:
            cache_id: The identifier for the cached data to delete

        Returns:
            True if item was deleted, False if it didn't exist
        """
        try:
            del self.cache[cache_id]
            return True
        except KeyError:
            return False

    def cache_exists(self, cache_id: str) -> bool:
        """
        Check if a cache entry exists.

        Args:
            cache_id: The identifier for the cached data

        Returns:
            True if the cache entry exists, False otherwise
        """
        return cache_id in self.cache


# Create a singleton instance to be imported
cache_service = CacheService()
