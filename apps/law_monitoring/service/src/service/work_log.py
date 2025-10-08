from typing import Dict, Optional

from loguru import logger

from service.core.utils.singleton import SingletonMeta
from service.law_core.models import (
    TaskStatus,
    WorkLog,
)


class WorkLogManager(metaclass=SingletonMeta):
    """Thread-safe singleton WorkLogManager for managing work logs.

    This class manages work logs for different execution tasks,
    providing thread-safe storage and retrieval operations.
    """

    def __init__(self) -> None:
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        logger.info("Initializing WorkLogManager")
        self._work_logs: Dict[str, WorkLog] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "WorkLogManager":
        """Get the singleton instance. Creates one if it doesn't exist."""
        return cls()

    def get(self, execution_id: str) -> Optional[WorkLog]:
        """Get a work log by execution ID."""
        return self._work_logs.get(execution_id)

    def set(self, execution_id: str, work_log: WorkLog) -> None:
        """Store a work log with the given execution ID."""
        self._work_logs[execution_id] = work_log

    def contains(self, execution_id: str) -> bool:
        """Check if a work log exists for the given execution ID."""
        return execution_id in self._work_logs

    def update_status(self, execution_id: str, status: TaskStatus) -> bool:
        """Update the status of a work log.

        Args:
            execution_id: The execution ID of the work log
            status: The new status to set

        Returns:
            True if the work log was found and updated, False otherwise
        """
        if execution_id in self._work_logs:
            self._work_logs[execution_id].status = status
            return True
        return False

    def remove(self, execution_id: str) -> bool:
        """Remove a work log by execution ID.

        Args:
            execution_id: The execution ID of the work log to remove

        Returns:
            True if the work log was found and removed, False otherwise
        """
        if execution_id in self._work_logs:
            del self._work_logs[execution_id]
            return True
        return False

    def get_all_ids(self) -> list[str]:
        """Get all execution IDs currently stored."""
        return list(self._work_logs.keys())

    def clear_all(self) -> None:
        """Clear all work logs (useful for testing or cleanup)."""
        self._work_logs.clear()
        logger.info("Cleared all work logs")


# Create a singleton instance to be imported
work_log_manager = WorkLogManager()
