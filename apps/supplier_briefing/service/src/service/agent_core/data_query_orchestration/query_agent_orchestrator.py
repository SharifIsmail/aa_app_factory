import inspect

from loguru import logger
from smolagents import (
    RunResult,
)

from service.agent_core.constants import REPO_AGENT_RESPONSE, REPO_INSIGHTS, AgentMode
from service.agent_core.data_query_orchestration.prompts.query_agent_prompts import (
    QUERY_AGENT_PROMPT,
)
from service.agent_core.hybrid_flow_agent import HybridFlowAgent
from service.agent_core.model_tools_manager import data_analysis_tool_name
from service.agent_core.models import FlowResponse, TaskStatus, WorkLog
from service.agent_core.work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.dependencies import with_settings


class QueryAgentOrchestrator:
    def __init__(self, work_log: WorkLog, execution_id: str) -> None:
        self.work_log = work_log
        self.execution_id = execution_id

    def check_cancelled(self) -> bool:
        if (
            self.work_log.status == TaskStatus.FAILED
            or self.work_log.status == TaskStatus.CANCELLED
        ):
            logger.warning(f"Query task {self.execution_id} has been cancelled")

            frame = inspect.currentframe()
            if frame is not None and frame.f_back is not None:
                calling_line = inspect.getframeinfo(frame.f_back).lineno
                logger.warning(
                    f"Cancellation detected at line {calling_line} in query execution"
                )
            else:
                logger.warning("Cancellation detected (unable to determine exact line)")
            return True
        return False

    def setup_worklog_environment(self) -> None:
        logger.info("Starting query task")
        logger.info(f"Execution ID: {self.execution_id}")
        logger.info("Setting up WorkLog data storage with tool-specific repositories")
        logger.info("Setting initial setup task status to IN_PROGRESS")
        update_task_status(self.work_log, TaskKeys.SETUP_TASK, TaskStatus.IN_PROGRESS)

    def execute_query_agent(
        self,
        query_agent: HybridFlowAgent,
        query: str,
        mode: AgentMode = AgentMode.AGENT,
        flow_name: str | None = None,
        params: dict | None = None,
    ) -> FlowResponse | RunResult:
        """Execute the query and store core results."""
        logger.info(f"Setting ANSWER_QUERY_TASK task status to IN_PROGRESS")
        update_task_status(
            self.work_log, TaskKeys.ANSWER_QUERY_TASK, TaskStatus.IN_PROGRESS
        )

        steps_count = len(query_agent.memory.steps)
        logger.info(
            f"AGENT_STEPS_COUNT: {steps_count} internal steps before starting query task"
        )

        logger.info(f"Query: {query}")
        logger.info(f"Execution mode: {mode.value}")

        if mode == AgentMode.AGENT:
            # Prepend orchestration prompt to the user query for agent mode
            settings = with_settings()
            preface = QUERY_AGENT_PROMPT.format(
                output_language=settings.target_output_language,
                data_analysis_tool_name=data_analysis_tool_name,
            )
            combined_query = f"{preface}\n\n User query: {query}"

            # Use the HybridFlowAgent's run method with agent mode
            result = query_agent.run(query=combined_query, reset=False, mode=mode)
        else:
            # For deterministic mode, pass parameters as-is
            result = query_agent.run(
                query=query,
                reset=False,
                mode=mode,
                flow_name=flow_name,
                flow_params=params or {},
            )

        # Store the final answer/result in the data storage
        self.work_log.data_storage.store_to_repo(
            REPO_AGENT_RESPONSE, "agent_response", result
        )
        logger.info("Stored final agent response in AGENT_RESPONSE repository")

        # Also store in REPO_INSIGHTS for insights tracking
        self.work_log.data_storage.store_to_repo(
            REPO_INSIGHTS, "agent_response", result
        )
        logger.info("Stored agent response in INSIGHTS repository")

        update_task_status(
            self.work_log, TaskKeys.ANSWER_QUERY_TASK, TaskStatus.COMPLETED
        )

        return result
