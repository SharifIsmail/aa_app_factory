from datetime import datetime, timedelta

from loguru import logger

from service.agent_core.models import FlowTask, TaskStatus, WorkLog


class TaskKeys:
    SETUP_TASK = "setup_task"
    ANSWER_QUERY_TASK = "answer_query_task"
    GENERATE_FINAL_ANSWER = "generate_final_answer"
    GENERATE_EXPLAINABILITY = "generate_explainability"


def create_work_log(
    work_log_id: str, expiration_seconds: int = 24 * 60 * 60
) -> WorkLog:
    setup_task = FlowTask(
        key=TaskKeys.SETUP_TASK,
        description="Setup des agentischen Systems",
        status=TaskStatus.PENDING,
    )

    answer_query_task = FlowTask(
        key=TaskKeys.ANSWER_QUERY_TASK,
        description="Abrufen von Daten aus der Datenbank mit Agenten",
        status=TaskStatus.PENDING,
    )

    generate_final_answer_task = FlowTask(
        key=TaskKeys.GENERATE_FINAL_ANSWER,
        description="Generierung der finalen Antwort",
        status=TaskStatus.PENDING,
    )

    generate_explainability = FlowTask(
        key=TaskKeys.GENERATE_EXPLAINABILITY,
        description="Erklärung der durchgeführten Schritte",
        status=TaskStatus.PENDING,
    )

    now = datetime.now()
    work_log = WorkLog(
        id=work_log_id,
        status=TaskStatus.PENDING,
        tasks=[
            setup_task,
            answer_query_task,
            generate_final_answer_task,
            generate_explainability,
        ],
        created_at=now,
        expires_at=now + timedelta(seconds=expiration_seconds),
    )

    work_log.task_type = "PANDAS_DATA_FETCH"

    return work_log


def are_all_tasks_completed(work_log: WorkLog) -> bool:
    """Check if all tasks in the work log are completed."""
    return all(task.status == TaskStatus.COMPLETED for task in work_log.tasks)


def complete_work_log_if_all_tasks_done(work_log: WorkLog) -> None:
    """Set work log status to COMPLETED only if all tasks are completed."""
    if are_all_tasks_completed(work_log):
        work_log.status = TaskStatus.COMPLETED
        logger.info("All tasks completed. Work log status set to COMPLETED.")
    else:
        incomplete_tasks = [
            task.key for task in work_log.tasks if task.status != TaskStatus.COMPLETED
        ]
        logger.info(f"Work log not completed. Incomplete tasks: {incomplete_tasks}")


def update_task_status(work_log: WorkLog, task_key: str, status: TaskStatus) -> None:
    """Update the status of a specific task in the work log."""
    task = work_log.get_single_task_with_key(task_key)
    if task:
        task.status = status
        logger.info(f"Updated task {task_key} status to {status}")
        complete_work_log_if_all_tasks_done(work_log)
    else:
        logger.warning(f"Task {task_key} not found in work log")
