from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TaskStatus(str, Enum):
    """Enum representing the possible states of a task."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    WARNING = "WARNING"


@dataclass
class Error:
    """Represents an error that occurred during task execution."""

    timestamp: datetime
    task_id: str
    message: str
    severity: str
    details: Optional[Dict] = None


@dataclass
class FlowTask:
    """Represents a single task or subtask in the process."""

    key: str
    description: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    subtasks: Optional[List["FlowTask"]] = None
    metadata: Optional[Dict] = None


@dataclass
class ProcessStatus:
    """Represents the overall status of a long-running process."""

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
    params: Dict[str, str]
    result: Optional[str] = None

    def __init__(
        self, tool_name: str, params: Dict[str, str], result: Optional[str] = None
    ):
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
    extracted_data: Dict = field(default_factory=dict)
    company_name: Optional[str] = None
    report_file_path: Optional[str] = None
    research_type: Optional[str] = None

    def __init__(
        self,
        id: str,
        status: TaskStatus,
        tasks: List[FlowTask],
        company_name: Optional[str] = None,
        research_type: Optional[str] = None,
    ):
        self.id = id
        self.status = status
        self.tasks = tasks
        self.tool_logs = []
        self.extracted_data = {}
        self.company_name = company_name
        self.report_file_path = None
        self.research_type = research_type

    def get_single_task_with_key(self, key: str) -> FlowTask:
        tasks = self.get_tasks_with_key(key)
        if len(tasks) == 0:
            raise ValueError(f"No task found with key {key}")
        if len(tasks) > 1:
            raise ValueError(f"Multiple tasks found with key {key}")
        return tasks[0]

    def get_tasks_with_key(self, key: str) -> List[FlowTask]:
        tasks = []
        for task in self.tasks:
            if task.key == key:
                tasks.append(task)
            if task.subtasks:
                tasks.extend(self._get_subtasks_with_key(task.subtasks, key))
        return tasks

    def _get_subtasks_with_key(
        self, subtasks: List[FlowTask], key: str
    ) -> List[FlowTask]:
        found_tasks = []
        for subtask in subtasks:
            if subtask.key == key:
                found_tasks.append(subtask)
            if subtask.subtasks:
                found_tasks.extend(self._get_subtasks_with_key(subtask.subtasks, key))
        return found_tasks
