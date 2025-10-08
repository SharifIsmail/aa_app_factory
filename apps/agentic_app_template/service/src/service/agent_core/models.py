import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class InsightData:
    title: str
    source_url: str
    value: str
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "title": self.title,
            "source_url": self.source_url,
            "value": self.value,
        }
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        else:
            result["timestamp"] = datetime.now().isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InsightData":
        return cls(
            title=data.get("title", ""),
            source_url=data.get("source_url", ""),
            value=data.get("value", ""),
            timestamp=data.get("timestamp"),
        )

    @classmethod
    def from_search_result(cls, result: Dict[str, Any]) -> "InsightData":
        source_url = result.get("source_url") or result.get("link") or ""
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        value = (
            f"{title}: {snippet}"
            if title and snippet
            else (title or snippet or str(result))
        )
        return cls(
            title=title,
            source_url=source_url,
            value=value,
            timestamp=result.get("timestamp") or datetime.now().isoformat(),
        )


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
        self.repositories: Dict[str, Dict[str, Any]] = {}

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
    def retrieve_all_from_repo(self, repo_key: str) -> Dict[str, Any]:
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


class InMemoryStorage(DataStorage):
    def define_repo(self, repo_key: str) -> bool:
        if repo_key not in self.repositories:
            self.repositories[repo_key] = {}
            return True
        return False

    def store_to_repo(self, repo_key: str, data_key: str, data_item: Any) -> None:
        if isinstance(data_item, str):
            data_item = {"data": data_item}
        data_item = self._preprocess_data_for_storage(data_item)
        logger.debug(
            f"Storing data in repo '{repo_key}' with key '{data_key}': {type(data_item).__name__}"
        )
        self.repositories[repo_key][data_key] = data_item

    def _preprocess_data_for_storage(self, data_item: Any) -> Any:
        if isinstance(data_item, datetime):
            return data_item.isoformat()
        elif isinstance(data_item, dict):
            return {
                k: self._preprocess_data_for_storage(v) for k, v in data_item.items()
            }
        elif isinstance(data_item, list):
            return [self._preprocess_data_for_storage(item) for item in data_item]
        else:
            return data_item

    def retrieve_all_from_repo(self, repo_key: str) -> Dict[str, Any]:
        return self.repositories[repo_key]

    def clear_repo(self, repo_key: str) -> None:
        self.repositories[repo_key] = {}

    def repo_length(self, repo_key: str) -> int:
        return len(self.repositories[repo_key])

    def to_json(self) -> str:
        return json.dumps(self.repositories, indent=2)

    def from_json(self, json_str: str) -> None:
        self.repositories = {}
        try:
            repositories = json.loads(json_str)
            if not isinstance(repositories, dict):
                raise ValueError(
                    f"Invalid JSON format: expected dictionary but got {type(repositories).__name__}"
                )
            for repo_key, repo_data in repositories.items():
                if isinstance(repo_data, dict):
                    self.define_repo(repo_key)
                    for data_key, data_item in repo_data.items():
                        self.store_to_repo(repo_key, data_key, data_item)
        except Exception as e:
            logger.error(f"Error loading JSON data: {str(e)}")
            raise


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Error:
    timestamp: datetime
    task_id: str
    message: str
    severity: str
    details: Optional[Dict] = None


@dataclass
class FlowTask:
    key: str
    description: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    subtasks: Optional[List["FlowTask"]] = None
    metadata: Optional[Dict] = None


@dataclass
class ProcessStatus:
    status: TaskStatus
    current_task_description: str
    tasks: List[FlowTask]
    progress_percentage: Optional[int] = None
    start_time: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    errors: List[Error] = field(default_factory=list)
    metadata: Optional[Dict] = None


@dataclass
class ToolLog:
    timestamp: datetime
    tool_name: str
    params: dict[str, Any]
    result: Optional[str] = None

    def __init__(
        self, tool_name: str, params: dict[str, Any], result: Optional[str] = None
    ) -> None:
        self.timestamp = datetime.now()
        self.tool_name = tool_name
        self.params = params
        self.result = result


@dataclass
class WorkLog:
    id: str
    status: TaskStatus
    tasks: List[FlowTask]
    tool_logs: List[ToolLog]
    data_storage: DataStorage
    core_data: Optional[str] = None
    report_file_path: Optional[str] = None
    research_type: str = ""

    def __init__(
        self,
        id: str,
        status: TaskStatus,
        tasks: List[FlowTask],
        core_data: Optional[str] = None,
    ) -> None:
        self.id = id
        self.status = status
        self.tasks = tasks
        self.tool_logs = []
        self.core_data = core_data
        self.report_file_path = None
        self.data_storage = InMemoryStorage()

    def get_single_task_with_key(self, key: str) -> FlowTask:
        tasks = self.get_tasks_with_key(key)
        if len(tasks) == 0:
            raise ValueError(f"No task found with key {key}")
        if len(tasks) > 1:
            raise ValueError(f"Multiple tasks found with key {key}")
        return tasks[0]

    def get_tasks_with_key(self, key: str) -> List[FlowTask]:
        tasks: List[FlowTask] = []
        for task in self.tasks:
            if task.key == key:
                tasks.append(task)
            if task.subtasks:
                tasks.extend(self._get_subtasks_with_key(task.subtasks, key))
        return tasks

    def _get_subtasks_with_key(
        self, subtasks: List[FlowTask], key: str
    ) -> List[FlowTask]:
        found_tasks: List[FlowTask] = []
        for subtask in subtasks:
            if subtask.key == key:
                found_tasks.append(subtask)
            if subtask.subtasks:
                found_tasks.extend(self._get_subtasks_with_key(subtask.subtasks, key))
        return found_tasks
