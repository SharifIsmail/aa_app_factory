import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence, Tuple

from smolagents import ActionStep, TaskStep, Tool
from smolagents.memory import ToolCall
from smolagents.monitoring import Timing

from service.agent_core.explainability.models import ExplainedActionStep
from service.agent_core.models import FlowResponse, SyntheticToolCall, WorkLog


class BaseDeterministicFlow(ABC):
    """Abstract base class for all deterministic agent flows."""

    def __init__(self, tools: Dict[str, Tool], work_log: WorkLog):
        """
        Initializes the flow with necessary dependencies.

        Args:
            tools: A dictionary of available tools.
            work_log: The work log for the current execution.
        """
        self.tools = tools
        self.work_log = work_log

    def push_deterministic_explained_action_step(self, text: str) -> None:
        """
        Records an observability step for progressive explainability.
        Appends to WorkLog.explained_steps for consistency with agent mode.

        Args:
            text: The explanation text for the step.
        """
        now = time.time()
        # Create an ExplainedActionStep compatible with the current architecture
        explained_step = ExplainedActionStep(
            explanation=text,
            time_start=now,
            time_end=now,
            executed_code="",
            execution_log="",
            code_output="",
            agent_name="deterministic_flow",
            step_number=len(self.work_log.explained_steps) + 1,
        )
        self.work_log.explained_steps.append(explained_step)

    def create_synthetic_action_step(
        self,
        start_time: float,
        thought: str,
        tool_calls: List[SyntheticToolCall],
        observations: List[str],
        action_output: str,
        step_number: int = 1,
    ) -> ActionStep:
        """
        Creates a synthetic ActionStep for agent memory.

        Args:
            start_time: The start time of the step (from time.time()).
            thought: The simulated agent "thought" process.
            tool_calls: A list of SyntheticToolCall objects representing tool calls.
            observations: A list of strings representing the results of tool calls.
            action_output: The final output message for the step.
            step_number: The step number for this action (defaults to 1 for backward compatibility).

        Returns:
            A populated ActionStep object.
        """
        action_step = ActionStep(
            step_number=step_number, timing=Timing(start_time=start_time)
        )
        action_step.model_output = f"Thought: {thought}"

        synthetic_tool_calls = [
            ToolCall(
                id=f"call_{i + 1}",
                name=call.name,
                arguments=json.dumps(call.arguments),
            )
            for i, call in enumerate(tool_calls)
        ]
        action_step.tool_calls = synthetic_tool_calls
        action_step.observations = "\n".join(observations)
        action_step.action_output = action_output

        return action_step

    @abstractmethod
    def run(
        self, flow_params: Dict[str, Any] | None = None
    ) -> Tuple[FlowResponse, Sequence[ActionStep | TaskStep]]:
        """
        Executes the deterministic flow.

        Args:
            flow_params: Parameters specific to this flow execution.

        Returns:
            A tuple containing:
            - A FlowResponse object containing the final message data to be returned to the user.
            - A list of synthetic ActionSteps that represent the flow's execution,
              to be injected into the agent's memory.
        """
        pass
