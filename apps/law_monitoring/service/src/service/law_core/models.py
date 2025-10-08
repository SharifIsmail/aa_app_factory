from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from service.storage.data_storage import DataStorage
from service.storage.in_memory_storage import InMemoryStorage


@dataclass
class SubjectMatter:
    """Data transfer object for subject matter extraction results."""

    key_stakeholder_roles: str
    revenue_based_penalties: str
    scope_subject_matter_summary: str


@dataclass
class Timeline:
    """Data transfer object for timeline extraction results."""

    timeline_content: str


@dataclass
class RolesPenalties:
    """Data transfer object for roles and penalties extraction results."""

    general_penalties_raw: str
    revenue_based_penalties_status: str
    penalty_severity_assessment_raw: str
    compliance_matrix_raw: str
    has_revenue_based_penalties: bool


@dataclass
class ReportPaths:
    """Data transfer object for generated report file paths."""

    html: str | None = None
    json: str | None = None
    pdf: str | None = None
    word: str | None = None


@dataclass
class LawSummaryData:
    """Structured data model for law summary reports passed to all generators."""

    # Core identification
    law_id: str
    source_link: str
    title: str

    metadata: dict[str, Any]
    processing_status: str

    header_raw: str
    subject_matter: SubjectMatter
    timeline: Timeline
    roles_penalties: RolesPenalties
    roles_raw: str

    # Team relevancy data
    team_relevancy_classification: list[dict[str, Any]]

    document_type_label: str
    oj_series_label: str
    business_areas_affected: str

    # Optional date fields
    publication_date: str | None = None
    document_date: str | None = None
    end_validity_date: str | None = None
    notification_date: str | None = None
    date_of_effect: str | None = None

    # Optional additional fields
    full_report_link: str | None = None


@dataclass
class InsightData:
    title: str
    source_url: str
    value: str
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> "InsightData":
        return cls(
            title=data.get("title", ""),
            source_url=data.get("source_url", ""),
            value=data.get("value", ""),
            timestamp=data.get("timestamp"),
        )

    @classmethod
    def from_search_result(cls, result: dict[str, Any]) -> "InsightData":
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
    details: dict | None = None


@dataclass
class FlowTask:
    key: str
    description: str
    status: TaskStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    subtasks: list["FlowTask"] | None = None
    metadata: dict | None = None


@dataclass
class ProcessStatus:
    status: TaskStatus
    current_task_description: str
    tasks: list[FlowTask]
    progress_percentage: int | None = None
    start_time: datetime | None = None
    estimated_completion_time: datetime | None = None
    errors: list[Error] = field(default_factory=list)
    metadata: dict | None = None


@dataclass
class ToolLog:
    timestamp: datetime
    tool_name: str
    params: dict[str, Any]
    result: str | None = None

    def __init__(
        self, tool_name: str, params: dict[str, Any], result: str | None = None
    ) -> None:
        self.timestamp = datetime.now()
        self.tool_name = tool_name
        self.params = params
        self.result = result


@dataclass
class WorkLog:
    id: str
    status: TaskStatus
    tasks: list[FlowTask]
    tool_logs: list[ToolLog]
    data_storage: DataStorage
    core_data: str | None = None
    report_file_path: str | None = None
    research_type: str = ""

    def __init__(
        self,
        id: str,
        status: TaskStatus,
        tasks: list[FlowTask],
        core_data: str | None = None,
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

    def get_tasks_with_key(self, key: str) -> list[FlowTask]:
        tasks: list[FlowTask] = []
        for task in self.tasks:
            if task.key == key:
                tasks.append(task)
            if task.subtasks:
                tasks.extend(self._get_subtasks_with_key(task.subtasks, key))
        return tasks

    def _get_subtasks_with_key(
        self, subtasks: list[FlowTask], key: str
    ) -> list[FlowTask]:
        found_tasks: list[FlowTask] = []
        for subtask in subtasks:
            if subtask.key == key:
                found_tasks.append(subtask)
            if subtask.subtasks:
                found_tasks.extend(self._get_subtasks_with_key(subtask.subtasks, key))
        return found_tasks
