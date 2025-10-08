from loguru import logger

from service.agent_core.models import FlowTask, TaskStatus, WorkLog


class TaskKeys:
    INITIAL_RESEARCH = "initial_research"
    RESEARCH_ITERATION = "research_iteration"
    GENERATE_RESEARCH_REPORT = "generate_research_report"


def create_work_log(research_type: str, work_log_id: str) -> WorkLog:
    # Compute num_iterations based on research_type
    num_iterations = 1 if research_type.lower() == "basic" else 5

    initial_research_task = FlowTask(
        key=TaskKeys.INITIAL_RESEARCH,
        description="Initiating research process",
        status=TaskStatus.PENDING,
    )

    iteration_subtasks = []
    for i in range(1, num_iterations + 1):
        iteration_task = FlowTask(
            key=f"{TaskKeys.RESEARCH_ITERATION}_{i}",
            description=f"Research iteration {i} of {num_iterations}",
            status=TaskStatus.PENDING,
        )
        iteration_subtasks.append(iteration_task)

    generate_report_task = FlowTask(
        key=TaskKeys.GENERATE_RESEARCH_REPORT,
        description="Generating assessment report",
        status=TaskStatus.PENDING,
    )

    work_log = WorkLog(
        id=work_log_id,
        status=TaskStatus.PENDING,
        tasks=[initial_research_task] + iteration_subtasks + [generate_report_task],
    )

    work_log.research_type = research_type

    return work_log


def update_task_status(work_log: WorkLog, task_key: str, status: TaskStatus) -> None:
    """Update the status of a specific task in the work log."""
    task = work_log.get_single_task_with_key(task_key)
    if task:
        task.status = status
        logger.info(f"Updated task {task_key} status to {status}")
    else:
        logger.warning(f"Task {task_key} not found in work log")


def get_task_status(work_log: WorkLog, task_key: str) -> TaskStatus | None:
    """Get the status of a specific task in the work log."""
    task = work_log.get_single_task_with_key(task_key)
    if task:
        return task.status
    logger.warning(f"Task {task_key} not found in work log")
    return None
