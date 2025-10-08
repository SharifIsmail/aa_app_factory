import base64
import glob
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional, Union

from filelock import FileLock, Timeout

from service.core.utils.singleton import SingletonMeta
from service.law_core.persistence.storage_backend import StorageBackend


class FilesystemStorageBackend(StorageBackend, metaclass=SingletonMeta):
    """
    Filesystem-based storage backend implementation.
    Manages its own storage directory internally with folder-based organization.
    Thread-safe and process-safe using filelock for cross-process coordination.
    Singleton class to ensure consistent behavior across the application.
    """

    _BINARY_MARKER = "FILESYSTEM_BASE64_BINARY:"

    def __init__(self) -> None:
        """
        Initialize filesystem backend with its own storage directory.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        # Create and manage our own storage directory
        self.base_directory = (
            Path(tempfile.gettempdir()) / "law_monitoring_data_storage"
        )
        self.base_directory.mkdir(parents=True, exist_ok=True)

        # File locking configuration
        self._lock_timeout = 5.0  # 5 second timeout to prevent deadlocks

        # Create locks directory for lock files in separate temp space
        self.locks_directory = Path(tempfile.gettempdir()) / "law_monitoring_locks"
        self.locks_directory.mkdir(exist_ok=True)

        self._initialized = True

    def _get_lock_file_path(self, folder: str, filename: str) -> str:
        """
        Generate a lock file path for the given folder and filename.

        Args:
            folder: Folder name
            filename: File name (or special keys like '_directory_')

        Returns:
            Path to the lock file
        """
        # Create a safe lock file name by replacing path separators
        safe_name = f"{folder}_{filename}".replace("/", "_").replace("\\", "_")
        lock_file = self.locks_directory / f"{safe_name}.lock"
        return str(lock_file)

    @contextmanager
    def _with_file_lock(
        self, folder: str, filename: str, allow_fallback: bool = False
    ) -> Generator[None, None, None]:
        """
        Context manager for file operations with cross-process locking.

        Args:
            folder: Folder name
            filename: File name (or special keys like '_directory_')
            allow_fallback: If True, continues without lock on timeout (for read-only ops)
        """
        lock_path = self._get_lock_file_path(folder, filename)
        lock = FileLock(lock_path, timeout=self._lock_timeout)

        try:
            with lock:
                yield
        except Timeout:
            if allow_fallback:
                # Continue without lock for read-only operations
                yield
            else:
                raise TimeoutError(
                    f"Could not acquire lock for {folder}/{filename} within {self._lock_timeout}s"
                )

    def _get_folder_path(self, folder: str) -> Path:
        """Get the full filesystem path for a folder."""
        # Prevent directory traversal attacks
        if ".." in folder or folder.startswith("/") or folder.startswith("\\"):
            raise ValueError(f"Invalid folder name: {folder}")

        # Additional security: resolve the path and ensure it's within base directory
        candidate_path = (self.base_directory / folder).resolve()
        base_path_resolved = self.base_directory.resolve()

        # Check if the resolved path is within the base directory
        try:
            candidate_path.relative_to(base_path_resolved)
        except ValueError:
            raise ValueError(f"Path traversal attempt detected: {folder}")

        return candidate_path

    def _get_full_path(self, folder: str, filename: str) -> Path:
        """Get the full filesystem path for a file in a folder."""
        folder_path = self._get_folder_path(folder)
        final_path = (folder_path / filename).resolve()

        # Ensure the final path is still within our folder
        try:
            final_path.relative_to(folder_path.resolve())
        except ValueError:
            raise ValueError(
                f"Invalid filename creates path outside folder: {filename}"
            )

        return final_path

    def save_file(self, folder: str, filename: str, content: Union[str, bytes]) -> str:
        """Save content to filesystem with cross-process file locking."""
        with self._with_file_lock(folder, filename):
            # Ensure folder exists
            self.create_folder(folder)

            full_path = self._get_full_path(folder, filename)

            if isinstance(content, bytes):
                # Encode binary content as base64 with marker
                encoded_content = base64.b64encode(content).decode("utf-8")
                file_content = f"{self._BINARY_MARKER}{encoded_content}"
            else:
                # Store text content as-is
                file_content = content

            # Always write as text (UTF-8)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                f.flush()  # Ensure data is written
                os.fsync(f.fileno())  # Force write to disk

            return str(full_path.absolute())

    def load_file(self, folder: str, filename: str) -> Optional[Union[str, bytes]]:
        """Load content from filesystem with cross-process file locking."""
        with self._with_file_lock(folder, filename):
            full_path = self._get_full_path(folder, filename)

            if full_path.exists():
                # Always read as text
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check if content is base64-encoded binary (same approach as PhariaData)
                if content.startswith(self._BINARY_MARKER):
                    # Remove marker and decode base64
                    encoded_content = content[len(self._BINARY_MARKER) :]
                    try:
                        return base64.b64decode(encoded_content)  # Returns bytes
                    except Exception as e:
                        raise ValueError(
                            f"Failed to decode base64 content for file '{filename}' in folder '{folder}': {e}"
                        ) from e
                else:
                    # Return text content as-is
                    return content  # Returns str
            return None

    def file_exists(self, folder: str, filename: str) -> bool:
        """Check if file exists on filesystem with optional locking."""
        with self._with_file_lock(folder, filename, allow_fallback=True):
            return self._get_full_path(folder, filename).exists()

    def list_files(self, folder: str, pattern: Optional[str] = None) -> List[str]:
        """List files in filesystem folder with cross-process locking."""
        with self._with_file_lock(folder, "_directory_"):
            folder_path = self._get_folder_path(folder)

            if not folder_path.exists():
                return []

            if pattern:
                # Use glob for pattern matching
                search_pattern = str(folder_path / pattern)
                matches = glob.glob(search_pattern)
                # Return just filenames (without folder path)
                return [Path(match).name for match in matches if Path(match).is_file()]

            # List all files in folder
            files = []
            for item in folder_path.iterdir():
                if item.is_file():
                    files.append(item.name)
            return files

    def delete_file(self, folder: str, filename: str) -> bool:
        """Delete file from filesystem with cross-process file locking."""
        try:
            with self._with_file_lock(folder, filename):
                full_path = self._get_full_path(folder, filename)

                if full_path.exists():
                    full_path.unlink()
                return True  # Success (file deleted or already gone)

        except Exception:
            return False

    def list_folders(self) -> List[str]:
        """List all folders in the storage backend."""
        try:
            with self._with_file_lock("_base_", "_directory_", allow_fallback=True):
                if not self.base_directory.exists():
                    return []

                folders = []
                for item in self.base_directory.iterdir():
                    if item.is_dir():
                        folders.append(item.name)
                return sorted(folders)

        except Exception:
            return []

    def create_folder(self, folder: str) -> bool:
        """Create a new folder with cross-process file locking."""
        try:
            with self._with_file_lock(folder, "_directory_"):
                folder_path = self._get_folder_path(folder)
                folder_path.mkdir(parents=True, exist_ok=True)
                return True

        except Exception:
            return False

    def get_files_in_folder(self, folder: str) -> List[str]:
        """Get all files in a specific folder."""
        return self.list_files(folder)


# Create a singleton instance to be imported
filesystem_storage_backend = FilesystemStorageBackend()
