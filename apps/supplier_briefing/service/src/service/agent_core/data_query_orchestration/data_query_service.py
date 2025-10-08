from typing import Any

from loguru import logger

from service.agent_core.cleanup_agent_state import cleanup_agent_state
from service.agent_core.constants import AgentMode
from service.agent_core.data_query_orchestration.agent_lifecycle import AgentLifecycle
from service.agent_core.data_query_orchestration.post_processor import PostProcessor
from service.agent_core.data_query_orchestration.query_agent_orchestrator import (
    QueryAgentOrchestrator,
)
from service.agent_core.models import TaskStatus, WorkLog
from service.agent_core.work_log_manager import (
    TaskKeys,
    create_work_log,
    update_task_status,
)
from service.settings import Settings
from service.work_log_manager import WorkLogManager


class DataQueryService:
    """Service for orchestrating data query processes."""

    def __init__(self, settings: Settings, work_log_manager: WorkLogManager):
        self.settings = settings
        self.work_log_manager = work_log_manager
        self.lifecycle = AgentLifecycle(settings)

    def run(
        self,
        query: str,
        execution_id: str,
        enable_explainability: bool = True,
        mode: AgentMode = AgentMode.AGENT,
        flow_name: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> WorkLog:
        query_agent = None
        work_log = None
        try:
            logger.info(f"Query: {query}")

            query_agent, tools, work_log = self.lifecycle.get_or_create_agent(
                execution_id, enable_explainability=enable_explainability
            )

            query_agent_executor = QueryAgentOrchestrator(
                work_log=work_log, execution_id=execution_id
            )

            self.work_log_manager.set(execution_id, work_log)

            if query_agent is None or query_agent_executor.check_cancelled():
                return work_log

            query_agent_executor.setup_worklog_environment()
            if query_agent_executor.check_cancelled():
                return work_log

            update_task_status(work_log, TaskKeys.SETUP_TASK, TaskStatus.COMPLETED)

            # Track start index of steps to only consider steps from this turn
            start_step_index = (
                len(query_agent.memory.steps) if query_agent is not None else 0
            )

            query_agent_executor.execute_query_agent(
                query_agent,
                query,
                mode=mode,
                flow_name=flow_name,
                params=params,
            )
            if query_agent_executor.check_cancelled():
                return work_log

            # Only pass steps created in this turn to the post-processor
            current_turn_steps = (
                query_agent.memory.steps[start_step_index:]
                if query_agent is not None
                else []
            )

            post_processor = PostProcessor(
                query=query,
                query_agent_memory_steps=current_turn_steps,
                work_log=work_log,
            )

            post_processor.post_process()

            update_task_status(
                work_log, TaskKeys.GENERATE_FINAL_ANSWER, TaskStatus.COMPLETED
            )

            # For deterministic flows, we need to mark explainability as complete
            # since we handle it directly in the flow (via push_step)
            if mode == AgentMode.DETERMINISTIC:
                update_task_status(
                    work_log, TaskKeys.GENERATE_EXPLAINABILITY, TaskStatus.COMPLETED
                )

            cleanup_agent_state(query_agent)

            # Mark the entire work log as completed
            work_log.status = TaskStatus.COMPLETED

            return work_log
        except Exception:
            logger.exception("Unhandled error in DataQueryService.run")
            if work_log is not None:
                work_log.status = TaskStatus.FAILED
                return work_log
            else:
                fallback_work_log = create_work_log(work_log_id=execution_id)
                fallback_work_log.status = TaskStatus.FAILED
                self.work_log_manager.set(execution_id, fallback_work_log)
                return fallback_work_log
        finally:
            try:
                if query_agent is not None:
                    cleanup_agent_state(query_agent)
            except Exception:
                pass
