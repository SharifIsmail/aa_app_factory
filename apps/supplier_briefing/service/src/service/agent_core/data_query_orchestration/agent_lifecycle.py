from typing import Dict, Optional, Tuple

from loguru import logger
from smolagents import Tool

from service.agent_core.constants import (
    REPO_AGENT_RESPONSE,
    REPO_INSIGHTS,
    REPO_PANDAS_OBJECTS,
    REPO_RESULTS,
)
from service.agent_core.explainability.explainability_service import (
    ExplainabilityService,
)
from service.agent_core.hybrid_flow_agent import HybridFlowAgent
from service.agent_core.initialize_models import initialize_models
from service.agent_core.model_tools_manager import (
    initialize_agents,
    initialize_tools,
)
from service.agent_core.models import TaskStatus, WorkLog
from service.agent_core.persistence import agent_instance_store
from service.agent_core.work_log_manager import create_work_log
from service.settings import Settings

CONVERSATION_TTL_SECONDS = 7 * 24 * 60 * 60


class AgentLifecycle:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_or_create_agent(
        self, execution_id: str, enable_explainability: bool = True
    ) -> Tuple[
        Optional[HybridFlowAgent],
        Dict[str, Tool],
        WorkLog,
    ]:
        if agent_instance_store.exists(execution_id):
            logger.info(f"Retrieving existing conversation for: {execution_id}")
            query_agent, work_log, tools = agent_instance_store.get_agent_with_data(  # type: ignore
                execution_id
            )
            logger.info(
                "Reusing existing agent with conversation history, data storage, and tools"
            )

            # Reset agent state and update callbacks for new conversation turn
            self.reset_old_worklog(work_log, execution_id)

            ExplainabilityService.get_single_instance().register_work_log(
                execution_id, work_log
            )
            ExplainabilityService.get_single_instance().set_enabled(
                enable_explainability
            )

            return query_agent, tools, work_log

        else:
            logger.info(f"Creating new conversation for: {execution_id}")
            work_log = create_work_log(
                work_log_id=execution_id,
                expiration_seconds=CONVERSATION_TTL_SECONDS,
            )

            models = initialize_models()

            ExplainabilityService.get_single_instance().register_work_log(
                execution_id, work_log
            )
            ExplainabilityService.get_single_instance().set_enabled(
                enable_explainability
            )

            tools = initialize_tools(models, execution_id, work_log, self.settings)

            agents = initialize_agents(models, tools, work_log, execution_id)

            code_agent = agents["query_agent"]

            # Wrap the CodeAgent in HybridFlowAgent
            query_agent = HybridFlowAgent(
                code_agent=code_agent,
                tools=tools,
                work_log=work_log,
            )

            # Store the complete conversation unit (agent + work_log + tools)
            logger.info(f"Storing new conversation for: {execution_id}")
            agent_instance_store.store_agent_with_data(
                execution_id, query_agent, work_log, tools
            )

            return query_agent, tools, work_log

    def reset_old_worklog(
        self,
        work_log: WorkLog,
        execution_id: str,
    ) -> None:
        work_log.status = TaskStatus.PENDING
        work_log.explained_steps = []

        # Reset all task statuses to PENDING for new query
        for task in work_log.tasks:
            task.status = TaskStatus.PENDING
            task.start_time = None
            task.end_time = None
            logger.info(f"Reset task '{task.key}' status to PENDING")

        # Clear all data storage repositories for fresh start
        repositories_to_clear = [
            REPO_INSIGHTS,
            REPO_AGENT_RESPONSE,
            REPO_RESULTS,
            REPO_PANDAS_OBJECTS,
        ]

        for repo_key in repositories_to_clear:
            try:
                work_log.data_storage.clear_repo(repo_key)
                logger.info(f"Cleared repository: {repo_key}")
            except Exception as e:
                logger.warning(f"Could not clear repository {repo_key}: {str(e)}")

        # Clear explanations and advance multi turn counter to isolate turns
        try:
            ExplainabilityService.get_single_instance().advance_multi_turn_counter(
                execution_id
            )
        except Exception as e:
            logger.warning(
                f"Could not clear explainability for {execution_id}: {str(e)}"
            )
