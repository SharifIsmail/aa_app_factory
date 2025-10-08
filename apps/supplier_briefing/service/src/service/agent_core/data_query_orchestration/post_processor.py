from loguru import logger
from smolagents import ActionStep, PlanningStep, TaskStep

from service.agent_core.constants import REPO_PANDAS_OBJECTS
from service.agent_core.models import TaskStatus, WorkLog
from service.agent_core.work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.utils import filter_agent_conversation_bloat


class PostProcessor:
    def __init__(
        self,
        query: str,
        query_agent_memory_steps: list[TaskStep | ActionStep | PlanningStep],
        work_log: WorkLog,
    ) -> None:
        self.query = query
        self.query_agent_memory_steps = query_agent_memory_steps
        self.work_log = work_log

    def post_process(self) -> None:
        update_task_status(
            self.work_log, TaskKeys.GENERATE_FINAL_ANSWER, TaskStatus.IN_PROGRESS
        )

        all_pandas_objects = self.work_log.data_storage.retrieve_all_from_repo(
            REPO_PANDAS_OBJECTS
        )
        logger.info(
            f"Retrieved {len(all_pandas_objects)} pandas objects query results from repository"
        )

        try:
            _ = self._filter_conversation_step()
        except Exception as e:
            logger.error(f"Post-processing conversation filtering failed: {str(e)}")
            logger.exception("Full post-processing error details:")

    def _filter_conversation_step(
        self,
    ) -> list[TaskStep | ActionStep | PlanningStep]:
        logger.info("Filtering conversation step")

        filtered_agent_steps = filter_agent_conversation_bloat(
            self.query_agent_memory_steps
        )

        logger.info(
            f"Conversation filtered from {len(self.query_agent_memory_steps)} to {len(filtered_agent_steps)} steps"
        )

        return filtered_agent_steps
