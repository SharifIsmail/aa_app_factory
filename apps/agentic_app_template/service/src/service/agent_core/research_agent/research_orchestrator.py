import json
from datetime import datetime
from typing import cast

from loguru import logger
from smolagents import CodeAgent, LiteLLMModel, Tool

from service.agent_core.models import TaskStatus, WorkLog
from service.agent_core.persistence_service import persistence_service
from service.agent_core.research_agent.model_tools_manager import (
    REPO_GOOGLE_SEARCH,
    REPO_RESEARCH_RESULTS,
    REPO_VISIT_WEBPAGE,
    initialize_agents,
    initialize_model,
    initialize_tools,
)
from service.agent_core.research_agent.research_prompts import (
    RESEARCH_AGENT_PROMPT,
    RESEARCH_AGENT_PROMPT_PREVIOUS_DATA,
)
from service.agent_core.research_agent.work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.agent_core.tools.xml_report_generator_tool import GenerateXMLReportTool
from service.settings import Settings


class ResearchAgentOrchestrator:
    """Orchestrates the research agent execution process."""

    def __init__(
        self, work_log: WorkLog, settings: Settings, execution_id: str
    ) -> None:
        self.work_log = work_log
        self.settings = settings
        self.execution_id = execution_id
        self.model: LiteLLMModel | None = None
        self.tools: dict[str, Tool] | None = None
        self.agents: dict[str, CodeAgent] | None = None

    def _check_cancelled(self) -> bool:
        """Check if the research task has been cancelled."""
        if (
            self.work_log.status == TaskStatus.FAILED
            or self.work_log.status == TaskStatus.CANCELLED
        ):
            logger.warning(f"Research task {self.execution_id} has been cancelled")
            # Log the cancellation point to help with debugging
            import inspect

            frame = inspect.currentframe()
            if frame is not None and frame.f_back is not None:
                calling_line = inspect.getframeinfo(frame.f_back).lineno
                logger.warning(
                    f"Cancellation detected at line {calling_line} in ResearchAgentOrchestrator"
                )
            else:
                logger.warning("Cancellation detected (unable to determine exact line)")
            return True
        return False

    def _initialize_components(self) -> bool:
        """Initialize model, tools, and agents. Returns True if successful, False if cancelled."""
        if self._check_cancelled():
            return False

        logger.info("Setting initial research task status to IN_PROGRESS")
        update_task_status(
            self.work_log, TaskKeys.INITIAL_RESEARCH, TaskStatus.IN_PROGRESS
        )

        logger.info("Initializing model...")
        self.model = initialize_model()
        logger.info("Model initialized successfully")

        if self._check_cancelled():
            return False

        logger.info("Initializing tools...")
        self.tools = initialize_tools(self.model, self.execution_id, self.work_log)
        logger.info("Tools initialized successfully")

        if self._check_cancelled():
            return False

        logger.info("Initializing agents...")
        self.agents = initialize_agents(self.model, self.tools, self.work_log)
        logger.info("Agents initialized successfully")

        logger.info("Setting initial research task status to COMPLETED")
        update_task_status(
            self.work_log, TaskKeys.INITIAL_RESEARCH, TaskStatus.COMPLETED
        )

        return True

    def _run_research_iteration(
        self, research_topic: str, iteration: int, num_iterations: int
    ) -> bool:
        """Run a single research iteration. Returns True if successful, False if cancelled."""
        if self._check_cancelled():
            return False

        logger.info(f"\n{'=' * 50}")
        logger.info(f"Starting iteration {iteration} of {num_iterations}")
        logger.info(f"{'=' * 50}\n")

        iteration_task_key = f"{TaskKeys.RESEARCH_ITERATION}_{iteration}"
        logger.info(f"Setting iteration {iteration} task status to IN_PROGRESS")
        update_task_status(self.work_log, iteration_task_key, TaskStatus.IN_PROGRESS)

        cache_file_iteration = f"cache_{research_topic}_iteration_{iteration}.json"
        logger.info(f"Checking for cached data in: {cache_file_iteration}")

        cached_data_storage = persistence_service.load_from_cache(cache_file_iteration)

        if cached_data_storage:
            logger.info("Found cached data!")
            try:
                # Handle either string or dictionary formats from cache
                json_str = (
                    cached_data_storage
                    if isinstance(cached_data_storage, str)
                    else json.dumps(cached_data_storage)
                )
                self.work_log.data_storage.from_json(json_str)
                logger.info("Successfully loaded cached data")
                update_task_status(
                    self.work_log, iteration_task_key, TaskStatus.COMPLETED
                )
                return True
            except Exception as e:
                logger.error(f"Error loading cached data: {str(e)}")
                logger.exception("Error loading cached data")
        else:
            logger.info("No cached data found, proceeding with new research")

        if self._check_cancelled():
            return False

        # Prepare research prompt
        logger.info("Preparing research prompt...")
        base_prompt = RESEARCH_AGENT_PROMPT.format(topic=research_topic)
        prompt = base_prompt
        logger.info("Prompt loaded.")

        google_search_data = self.work_log.data_storage.retrieve_all_from_repo(
            REPO_GOOGLE_SEARCH
        )
        if len(google_search_data) > 0:
            logger.info("Adding previous data to prompt...")
            queue_summary = json.dumps(list(google_search_data.values()), indent=2)
            prompt += RESEARCH_AGENT_PROMPT_PREVIOUS_DATA.format(
                old_incident_queue=queue_summary
            )
            logger.info("Previous data added to prompt")

        self._log_repository_stats()
        logger.info(f"Prompt length: {len(prompt)} characters")

        if self._check_cancelled():
            return False

        # Run the research agent
        logger.info("Running research agent...")

        # Check if agents is None before accessing
        if self.agents is None:
            logger.error("Agents not initialized")
            return False

        research_agent = self.agents["research_agent"]
        logger.info("Research agent configuration:")

        # Check if model is None before accessing its attributes
        if self.model is None:
            logger.error("Model not initialized")
            return False

        logger.info(f"- Model: {self.model.model_id}")
        logger.info(
            f"- Tools available: {[getattr(tool, 'name', str(tool)) for tool in research_agent.tools]}"
        )
        logger.info(f"- Max steps: {research_agent.max_steps}")

        logger.info("Starting agent execution...")
        result = research_agent.run(prompt)

        if self._check_cancelled():
            return False

        logger.info("Research agent completed successfully")
        logger.info(f"Agent result type: {type(result)}")
        logger.info(
            f"Agent result length: {len(str(result)) if result else 0} characters"
        )

        # Store the result
        result_key = f"result_iteration_{iteration}"
        self.work_log.data_storage.store_to_repo(
            REPO_RESEARCH_RESULTS,
            result_key,
            {
                "iteration": iteration,
                "result": result if result else "",
                "timestamp": datetime.now().isoformat(),
            },
        )

        if self._check_cancelled():
            return False

        # Save to cache
        logger.info("Saving to cache...")
        cache_data = self.work_log.data_storage.to_json()
        logger.info(f"Cache data size: {len(cache_data)} bytes")

        self._log_repository_stats_detailed()
        persistence_service.save_to_cache(cache_file_iteration, cache_data)
        logger.info("Cache saved successfully")

        logger.info(f"Setting iteration {iteration} task status to COMPLETED")
        update_task_status(self.work_log, iteration_task_key, TaskStatus.COMPLETED)
        logger.info(
            f"Iteration {iteration} complete. Google Search repository now contains {self.work_log.data_storage.repo_length(REPO_GOOGLE_SEARCH)} items."
        )

        return True

    def _log_repository_stats(self) -> None:
        """Log current repository statistics."""
        logger.info(
            f"Google Search repository size: {self.work_log.data_storage.repo_length(REPO_GOOGLE_SEARCH)}"
        )
        logger.info(
            f"Visit Webpage repository size: {self.work_log.data_storage.repo_length(REPO_VISIT_WEBPAGE)}"
        )
        logger.info(
            f"Research Results repository size: {self.work_log.data_storage.repo_length(REPO_RESEARCH_RESULTS)}"
        )

    def _log_repository_stats_detailed(self) -> None:
        """Log detailed repository statistics."""
        logger.info("Repository stats before cache saving:")
        for repo_key in self.work_log.data_storage.repositories.keys():
            try:
                repo_size = self.work_log.data_storage.repo_length(repo_key)
                logger.info(f" - {repo_key}: {repo_size} items")
            except Exception as e:
                logger.error(f"Error getting size for repo {repo_key}: {e}")

    def run(self, research_topic: str) -> str:
        """Run the complete research process.

        Args:
            research_topic: The topic to research

        Returns:
            str: Empty string (agent result is stored in WorkLog repositories)
        """
        logger.info("Starting research process")
        logger.info(f"Research topic: {research_topic}")
        logger.info(f"Execution ID: {self.execution_id}")

        if self._check_cancelled():
            return ""

        # Determine research type and iterations
        research_type = (
            self.work_log.research_type
            if hasattr(self.work_log, "research_type")
            else "comprehensive"
        )
        research_type = research_type.lower()
        num_iterations = 1 if research_type == "basic" else 5

        logger.info(f"Research type: {research_type}")
        logger.info(f"Number of iterations: {num_iterations}")

        logger.info("Setting up WorkLog data storage with tool-specific repositories")

        # Initialize components
        if not self._initialize_components():
            return ""

        # Run research iterations
        for iteration in range(1, num_iterations + 1):
            if not self._run_research_iteration(
                research_topic, iteration, num_iterations
            ):
                return ""

        logger.info("\nResearch agent orchestration completed successfully!")
        return ""

    @property
    def xml_generator_tool(self) -> GenerateXMLReportTool | None:
        """Get the XML generator tool for report generation."""
        if self.tools is None:
            return None
        tool = self.tools.get("xml_generator_tool")
        if tool is None:
            return None
        # Type cast since we know this tool should be GenerateXMLReportTool
        return cast(GenerateXMLReportTool, tool)
