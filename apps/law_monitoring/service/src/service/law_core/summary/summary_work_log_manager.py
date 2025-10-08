from datetime import datetime
from enum import Enum

from loguru import logger

from service.law_core.models import FlowTask, TaskStatus, WorkLog


class TaskKeys(Enum):
    FETCH_LAW = "FETCH_LAW"
    COMPUTE_IMPACT_ON_EACH_TEAM = "COMPUTE_IMPACT_ON_EACH_TEAM"

    # Header Data Analysis
    EXTRACT_HEADER = "EXTRACT_HEADER"

    # Document Content Analysis
    EXTRACT_SUBJECT_MATTER = "EXTRACT_SUBJECT_MATTER"
    EXTRACT_TIMELINE = "EXTRACT_TIMELINE"
    EXTRACT_DEFINITIONS = "EXTRACT_DEFINITIONS"

    # Combined Roles, Responsibilities and Penalties
    EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES = (
        "EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES"
    )

    GENERATE_REPORT = "GENERATE_REPORT"


def create_work_log(work_log_id: str) -> WorkLog:
    """Create a work log for law summary analysis tasks."""
    fetch_law_task = FlowTask(
        key=TaskKeys.FETCH_LAW.value,
        description="Retrieve the full legal text from the source",
        status=TaskStatus.PENDING,
    )

    extract_header_task = FlowTask(
        key=TaskKeys.EXTRACT_HEADER.value,
        description="Extract document metadata including title, effective date, type, and penalties summary",
        status=TaskStatus.PENDING,
    )

    extract_subject_matter_task = FlowTask(
        key=TaskKeys.EXTRACT_SUBJECT_MATTER.value,
        description="Analyze articles 1-2 to extract subject matter",
        status=TaskStatus.PENDING,
    )

    compute_team_relevancy_task = FlowTask(
        key=TaskKeys.COMPUTE_IMPACT_ON_EACH_TEAM.value,
        description="Determine relevance of the legal act for each team",
        status=TaskStatus.PENDING,
    )

    extract_timeline_task = FlowTask(
        key=TaskKeys.EXTRACT_TIMELINE.value,
        description="Extract timeline and compliance deadlines",
        status=TaskStatus.PENDING,
    )

    extract_definitions_task = FlowTask(
        key=TaskKeys.EXTRACT_DEFINITIONS.value,
        description="Extract and analyze the definitions section (typically article 3)",
        status=TaskStatus.PENDING,
    )

    extract_roles_responsibilities_penalties_task = FlowTask(
        key=TaskKeys.EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES.value,
        description="Extract roles, responsibilities, and associated penalties in a unified compliance matrix",
        status=TaskStatus.PENDING,
    )

    generate_report_task = FlowTask(
        key=TaskKeys.GENERATE_REPORT.value,
        description="Generate final analysis report",
        status=TaskStatus.PENDING,
    )

    work_log = WorkLog(
        id=work_log_id,
        status=TaskStatus.PENDING,
        tasks=[
            fetch_law_task,
            extract_header_task,
            extract_subject_matter_task,
            compute_team_relevancy_task,
            extract_timeline_task,
            # extract_definitions_task,
            extract_roles_responsibilities_penalties_task,
            generate_report_task,
        ],
    )
    return work_log


def update_task_status(
    work_log: WorkLog, task_key: TaskKeys, status: TaskStatus
) -> None:
    """Update the status of a specific task in the work log."""
    # Import metrics here to avoid circular imports
    from service.metrics import law_processing_step_duration_seconds

    task = work_log.get_single_task_with_key(task_key.value)
    if task:
        current_time = datetime.now()

        # Add timing when task starts
        if status == TaskStatus.IN_PROGRESS:
            task.start_time = current_time
        # Calculate duration when task completes or fails
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and task.start_time:
            task.end_time = current_time
            duration = (current_time - task.start_time).total_seconds()
            law_processing_step_duration_seconds.labels(
                step_name=task_key.value, status=status.value.lower()
            ).observe(duration)
            logger.info(f"Task {task_key.value} completed in {duration:.2f} seconds")

        task.status = status
        logger.info(f"Updated task {task_key.value} status to {status}")
    else:
        logger.warning(f"Task {task_key.value} not found in work log")


def get_task_status(work_log: WorkLog, task_key: TaskKeys) -> TaskStatus | None:
    """Get the status of a specific task in the work log."""
    task = work_log.get_single_task_with_key(task_key.value)
    if task:
        return task.status
    logger.warning(f"Task {task_key.value} not found in work log")
    return None
