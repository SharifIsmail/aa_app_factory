from __future__ import annotations

from typing import Any, Sequence

from loguru import logger
from smolagents import ActionStep, CodeAgent, RunResult, TaskStep, Tool
from smolagents.memory import AgentMemory

from service.agent_core.constants import AgentMode
from service.agent_core.deterministic_flows import DETERMINISTIC_FLOWS
from service.agent_core.models import FlowResponse, WorkLog


class HybridFlowAgent:
    """
    Wrapper class that encapsulates both agent and deterministic execution modes.

    This class acts as a unified interface for running either:
    - Traditional AI agent queries (via smolagents CodeAgent)
    - Deterministic flows with predefined logic
    """

    def __init__(
        self,
        code_agent: CodeAgent,
        tools: dict[str, Tool],
        work_log: WorkLog,
    ) -> None:
        """
        Initialize the hybrid agent wrapper.

        Args:
            code_agent: The underlying smolagents CodeAgent for AI-powered execution
            tools: Dictionary of available tools
            work_log: Work log for tracking execution
        """
        self._code_agent = code_agent
        self.tools = tools
        self.work_log = work_log

    def _run_agent(self, query: str, reset: bool = False) -> Any | RunResult:
        """Run in traditional agent mode using the CodeAgent."""
        logger.info("Executing in AGENT mode")
        return self._code_agent.run(task=query, reset=reset)

    def _inject_deterministic_run_into_memory(
        self,
        original_query: str | None,
        flow_name: str | None,
        flow_params: dict | None,
        synthetic_steps: Sequence[TaskStep | ActionStep],
    ) -> None:
        """Inject synthetic steps from deterministic flow into agent's memory.

        This maintains conversation continuity by making deterministic executions
        appear as part of the agent's conversation history.
        """
        # Create initial TaskStep describing what happened
        task_description = ""
        if original_query:
            task_description = f"User asked: '{original_query}'. "

        flow_description = f"Deterministic flow '{flow_name}' triggered"
        if flow_params:
            params_str = ", ".join(f"{k}={v}" for k, v in flow_params.items())
            flow_description += f" with parameters: {params_str}"

        task_description += f"{flow_description}."

        # Create the initial TaskStep
        task_step = TaskStep(task=task_description)

        # Inject steps into agent's memory
        # If smolagents changes their API, this will fail with a clear AttributeError
        self._code_agent.memory.steps.append(task_step)
        self._code_agent.memory.steps.extend(synthetic_steps)
        logger.info(f"Injected {len(synthetic_steps) + 1} steps into agent memory")

    def _run_deterministic(
        self,
        query: str | None = None,
        flow_name: str | None = None,
        flow_params: dict | None = None,
    ) -> FlowResponse | RunResult:
        """Run in deterministic mode using predefined flows."""
        logger.info(f"Executing deterministic flow: {flow_name}")

        # Validate flow_name
        if flow_name is None:
            raise ValueError("flow_name is required for deterministic mode")
        if flow_name not in DETERMINISTIC_FLOWS:
            raise ValueError(f"Unknown flow: {flow_name}")

        # Look up and instantiate the flow class
        flow_class = DETERMINISTIC_FLOWS[flow_name]
        flow_instance = flow_class(tools=self.tools, work_log=self.work_log)

        # Run the flow and get results + synthetic steps
        final_message, synthetic_steps = flow_instance.run(flow_params=flow_params)

        # Inject the synthetic steps into agent memory for continuity
        self._inject_deterministic_run_into_memory(
            original_query=query,
            flow_name=flow_name,
            flow_params=flow_params,
            synthetic_steps=synthetic_steps,
        )

        logger.info(f"Deterministic flow '{flow_name}' completed successfully")
        return final_message

    def run(
        self,
        query: str | None = None,
        reset: bool = False,
        mode: AgentMode = AgentMode.AGENT,
        flow_name: str | None = None,
        flow_params: dict | None = None,
    ) -> FlowResponse | RunResult:
        """
        Main execution method that routes to appropriate handler based on mode.

        Args:
            query: The user's query text
            reset: Whether to reset agent memory
            mode: Execution mode (AGENT or DETERMINISTIC)
            flow_name: Name of deterministic flow (required for DETERMINISTIC mode)
            flow_params: Parameters for deterministic flow

        Returns:
            Result from either agent or deterministic execution
        """
        if mode == AgentMode.AGENT:
            if query is None:
                raise ValueError("query is required in agent mode")
            return self._run_agent(query=query, reset=reset)
        elif mode == AgentMode.DETERMINISTIC:
            return self._run_deterministic(
                query=query, flow_name=flow_name, flow_params=flow_params
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")

    # Properties to maintain compatibility with CodeAgent interface
    @property
    def memory(self) -> AgentMemory:
        """Access the underlying agent's memory."""
        return self._code_agent.memory

    @property
    def step_callbacks(self) -> Any:
        """Access the underlying agent's step callbacks."""
        return self._code_agent.step_callbacks

    @property
    def monitor(self) -> Any:
        """Access the underlying agent's monitor."""
        return self._code_agent.monitor
