import re
from datetime import datetime

from loguru import logger
from smolagents import ActionStep, Timing, parse_code_blobs

from service.agent_core.explainability.explainability_client import (
    NO_DATA_OPERATIONS_STRING,
    ExplainabilityLLMClient,
)
from service.agent_core.explainability.models import ExplainedActionStep
from service.agent_core.models import ToolLog


class ExplainabilityProcessor:
    """
    Stateless processor that turns an `ActionStep` into an optional
    `ExplainedActionStep`, using tool logs and an injected LLM client.
    """

    def __init__(self, llm_client: ExplainabilityLLMClient) -> None:
        self._llm_client = llm_client

    @staticmethod
    def _extract_execution_log_and_code_output_from_execution_step_observation(
        step_observation: str,
    ) -> tuple[str, str]:
        """
        Parse step observation string to extract execution logs and code output.

        Returns:
            Tuple of (execution_log, code_output)
        """
        execution_logs_match = re.search(
            r"Execution logs:\s*(.*?)\s*Last output from code snippet:",
            step_observation,
            re.DOTALL,
        )
        code_output_match = re.search(
            r"Last output from code snippet:\s*(.*?)$", step_observation, re.DOTALL
        )

        execution_log = (
            execution_logs_match.group(1).strip() if execution_logs_match else ""
        )
        code_output = code_output_match.group(1).strip() if code_output_match else ""

        return execution_log, code_output

    @staticmethod
    def _filter_tool_logs_by_timing(
        tool_logs: list[ToolLog],
        step_timing: Timing,
    ) -> list[ToolLog]:
        """
        Filter tool logs to include only those within the specified time range.
        """
        start_datetime = datetime.fromtimestamp(step_timing.start_time)
        end_datetime = (
            datetime.fromtimestamp(step_timing.end_time)
            if step_timing.end_time is not None
            else None
        )

        filtered_logs: list[ToolLog] = []
        for log in tool_logs:
            if log.timestamp >= start_datetime:
                if end_datetime is None or log.timestamp <= end_datetime:
                    filtered_logs.append(log)

        return filtered_logs

    def explain_single_action_step_if_possible(
        self,
        step: ActionStep,
        tool_logs: list[ToolLog],
        agent_name: str,
    ) -> ExplainedActionStep | None:
        """Generates explanation of a single ActionStep. Returns None if ActionStep had an error or no model_output"""
        try:
            if step.model_output is not None and step.error is None:
                relevant_tool_logs = self._filter_tool_logs_by_timing(
                    tool_logs, step.timing
                )

                explanation = self._llm_client.generate_explanation(
                    step_model_output=str(step.model_output)
                    + "\nObservations: "
                    + str(step.observations),
                    tool_logs=relevant_tool_logs,
                )

                if NO_DATA_OPERATIONS_STRING in explanation:
                    return None

                execution_log, code_output = (
                    self._extract_execution_log_and_code_output_from_execution_step_observation(
                        str(step.observations)
                    )
                )

                executed_code = parse_code_blobs(
                    str(step.model_output), ("```python", "```")
                )

                return ExplainedActionStep(
                    executed_code=executed_code,
                    execution_log=execution_log,
                    code_output=code_output,
                    explanation=explanation,
                    time_start=step.timing.start_time,
                    time_end=step.timing.end_time,
                    agent_name=agent_name,
                    step_number=step.step_number,
                )
            else:
                logger.warning(f"ActionStep {step.step_number} without model_output")
                return None

        except Exception as e:
            logger.error(f"Error processing step {step.step_number}: {e}")
            return None
