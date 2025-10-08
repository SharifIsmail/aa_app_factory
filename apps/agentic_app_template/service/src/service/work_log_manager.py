from typing import Dict, Optional

from loguru import logger

from service.agent_core.models import (
    TaskStatus,
    WorkLog,
)


class WorkLogManager:
    _instance: Optional["WorkLogManager"] = None

    def __new__(cls) -> "WorkLogManager":
        if cls._instance is None:
            logger.info("Creating WorkLogManager singleton instance")
            cls._instance = super(WorkLogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self, "_initialized", False):
            # Simple dictionary storage - no locks
            self._work_logs: Dict[str, WorkLog] = {}
            self._initialized = True

    @classmethod
    def get_instance(cls) -> "WorkLogManager":
        if cls._instance is None:
            cls._instance = WorkLogManager()
        return cls._instance

    def get(self, execution_id: str) -> Optional[WorkLog]:
        return self._work_logs.get(execution_id)

    def set(self, execution_id: str, work_log: WorkLog) -> None:
        self._work_logs[execution_id] = work_log

    def contains(self, execution_id: str) -> bool:
        return execution_id in self._work_logs

    def update_status(self, execution_id: str, status: TaskStatus) -> bool:
        if execution_id in self._work_logs:
            self._work_logs[execution_id].status = status
            return True
        return False
