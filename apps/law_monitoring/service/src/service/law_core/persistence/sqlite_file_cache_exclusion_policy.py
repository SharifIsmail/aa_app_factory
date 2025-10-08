import fnmatch
from typing import List, Optional

from service.law_core.background_work.workers_constants import DATA_FOLDER


class SqliteFileCacheExclusionPolicy:
    """
    Policy for determining which folders/files should be excluded from caching.

    Features:
    - Glob pattern matching for flexible exclusion rules
    - Folder and file-level exclusion support
    - Default patterns for common exclusions
    """

    def __init__(self, exclusion_patterns: Optional[List[str]] = None):
        """
        Initialize exclusion policy.

        Args:
            exclusion_patterns: List of glob patterns for exclusion. If None, uses defaults.
        """
        self._patterns = exclusion_patterns or self._get_default_patterns()

    def _get_default_patterns(self) -> List[str]:
        """Get default exclusion patterns."""
        return [
            DATA_FOLDER,  # "data" folder and all its contents
            f"{DATA_FOLDER}/*",  # All files in data folder (recursive)
        ]

    def should_cache(self, folder: str, filename: Optional[str] = None) -> bool:
        """
        Determine if a folder/file should be cached.

        Args:
            folder: Folder name
            filename: Optional filename for file-specific checks

        Returns:
            True if should be cached, False if should be excluded
        """
        full_path = f"{folder}/{filename}" if filename else folder

        for pattern in self._patterns:
            if fnmatch.fnmatch(full_path, pattern):
                return False

        return True

    def add_pattern(self, pattern: str) -> None:
        """Add a new exclusion pattern."""
        if pattern not in self._patterns:
            self._patterns.append(pattern)

    def remove_pattern(self, pattern: str) -> None:
        """Remove an exclusion pattern."""
        if pattern in self._patterns:
            self._patterns.remove(pattern)

    def get_patterns(self) -> List[str]:
        """Get current exclusion patterns."""
        return self._patterns.copy()
