from abc import ABC, abstractmethod
from typing import Any


class DataStorage(ABC):
    """Abstract base class for managing multiple data repositories.

    This class provides a flexible storage system that can maintain multiple repositories,
    each acting as a separate key-value store. It's designed to be extended with different
    storage implementations (e.g., in-memory, database, file-based) while maintaining
    a consistent interface.

    The storage system is organized as follows:
    - Each repository is identified by a unique key (repo_key)
    - Each repository contains key-value pairs where:
        - Keys are data identifiers (data_key)
        - Values can be any type of data (data_item)

    Example:
        storage = InMemoryStorage()
        storage.define_repo("user_data")
        storage.store_to_repo("user_data", "user1", {"name": "John", "age": 30})
        data = storage.retrieve_all_from_repo("user_data")
    """

    def __init__(self) -> None:
        """Initialize the storage system with an empty repository dictionary."""
        self.repositories: dict[str, dict[str, Any]] = {}

    @abstractmethod
    def define_repo(self, repo_key: str) -> bool:
        """Create a new empty repository.

        Args:
            repo_key: Unique identifier for the new repository

        Returns:
            bool: True if repository was created, False if it already existed
        """
        pass

    @abstractmethod
    def store_to_repo(self, repo_key: str, data_key: str, data_item: Any) -> None:
        """Store data in a specific repository.

        Args:
            repo_key: Identifier of the target repository
            data_key: Key to store the data under
            data_item: Data to store (can be any type)

        Raises:
            KeyError: If repository doesn't exist
        """
        pass

    @abstractmethod
    def retrieve_all_from_repo(self, repo_key: str) -> dict[str, Any]:
        """Retrieve all data from a specific repository.

        Args:
            repo_key: Identifier of the repository to retrieve from

        Returns:
            Dict[str, Any]: All data stored in the repository

        Raises:
            KeyError: If repository doesn't exist
        """
        pass

    @abstractmethod
    def clear_repo(self, repo_key: str) -> None:
        """Remove all data from a specific repository.

        Args:
            repo_key: Identifier of the repository to clear

        Raises:
            KeyError: If repository doesn't exist
        """
        pass

    @abstractmethod
    def repo_length(self, repo_key: str) -> int:
        """Get the number of items in a specific repository.

        Args:
            repo_key: Identifier of the repository to check

        Returns:
            int: Number of items in the repository

        Raises:
            KeyError: If repository doesn't exist
        """
        pass

    @abstractmethod
    def to_json(self) -> str:
        """Convert the entire storage state to JSON format.

        Returns:
            str: JSON representation of all repositories and their data
        """
        pass

    @abstractmethod
    def from_json(self, json_str: str) -> None:
        """Load storage state from JSON format.

        Args:
            json_str: JSON string containing the storage state

        Raises:
            ValueError: If JSON format is invalid
            KeyError: If required repositories don't exist
        """
        pass
