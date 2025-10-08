from enum import Enum
from typing import List, Optional, Union


class StorageBackendType(Enum):
    """Enum for available storage backend types."""

    FILESYSTEM = "filesystem"
    PHARIA_DATA = "pharia_data"
    PHARIA_DATA_SYNCED_SQLITE = "pharia_data_synced_sqlite"


class StorageBackend:
    """
    Abstract base class for storage backends.
    Defines the interface that all storage implementations must follow.
    Files are organized in folders, not at root level.

    Note: This class doesn't use ABC to avoid metaclass conflicts with SingletonMeta.
    All methods should be overridden by subclasses.
    """

    def save_file(self, folder: str, filename: str, content: Union[str, bytes]) -> str:
        """
        Save content to a file in the specified folder.

        Args:
            folder: Folder where to save the file
            filename: Name of the file (without path)
            content: Content to save (string for text files, bytes for binary files)

        Returns:
            Backend-specific identifier where the file was saved
        """
        raise NotImplementedError("save_file must be implemented by subclasses")

    def load_file(self, folder: str, filename: str) -> Optional[Union[str, bytes]]:
        """
        Load content from a file in the specified folder.

        Args:
            folder: Folder containing the file
            filename: Name of the file (without path)

        Returns:
            File content if exists, None otherwise. Returns bytes for binary files.
        """
        raise NotImplementedError("load_file must be implemented by subclasses")

    def file_exists(self, folder: str, filename: str) -> bool:
        """
        Check if a file exists in the specified folder.

        Args:
            folder: Folder to check
            filename: Name of the file (without path)

        Returns:
            True if file exists, False otherwise
        """
        raise NotImplementedError("file_exists must be implemented by subclasses")

    def list_files(self, folder: str, pattern: Optional[str] = None) -> List[str]:
        """
        List files in a specific folder.

        Args:
            folder: Folder to list files from
            pattern: Optional glob pattern to filter files

        Returns:
            List of filenames (without folder path)
        """
        raise NotImplementedError("list_files must be implemented by subclasses")

    def delete_file(self, folder: str, filename: str) -> bool:
        """
        Delete a file from the specified folder.

        Args:
            folder: Folder containing the file
            filename: Name of the file (without path)

        Returns:
            True if deletion successful, False otherwise
        """
        raise NotImplementedError("delete_file must be implemented by subclasses")

    def list_folders(self) -> List[str]:
        """
        List all folders in the storage backend.

        Returns:
            List of folder names
        """
        raise NotImplementedError("list_folders must be implemented by subclasses")

    def create_folder(self, folder: str) -> bool:
        """
        Create a new folder in the storage backend.

        Args:
            folder: Name of the folder to create

        Returns:
            True if folder was created or already exists, False on failure
        """
        raise NotImplementedError("create_folder must be implemented by subclasses")

    def get_files_in_folder(self, folder: str) -> List[str]:
        """
        Get all files in a specific folder.

        Args:
            folder: Folder to get files from

        Returns:
            List of filenames (without folder path)
        """
        raise NotImplementedError(
            "get_files_in_folder must be implemented by subclasses"
        )
