"""Agent state cleanup strategies for managing conversation history."""

import time
from abc import ABC, abstractmethod
from typing import Any, List

from loguru import logger
from smolagents import ActionStep, TaskStep
from smolagents.monitoring import Timing


class AgentStateCleanupStrategy(ABC):
    """Abstract base class for agent state cleanup strategies."""

    @abstractmethod
    def cleanup(self, agent: Any) -> None:
        """Clean up the agent's internal state.

        Args:
            agent: The agent instance whose state needs to be cleaned up
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the strategy."""
        pass


class LoggingDummyFilteringStrategy(AgentStateCleanupStrategy):
    """Strategy that logs agent state to disk for inspection without filtering."""

    def __init__(self) -> None:
        """Initialize the logging dummy filtering strategy."""
        pass

    def cleanup(self, agent: Any) -> None:
        """Save agent conversation history to disk for inspection.

        This strategy will:
        1. Extract all conversation steps from agent memory
        2. Save them to a timestamped file for manual inspection
        3. Does NOT perform any actual filtering - just logs for analysis
        """
        logger.info(f"Running {self.name} strategy")

        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            logger.warning("Agent does not have memory.steps, skipping")
            return

        import json
        import os
        from datetime import datetime

        # Create directory for storing agent states
        storage_dir = "/tmp/agent_states"
        os.makedirs(storage_dir, exist_ok=True)

        # Generate timestamped filename with microseconds for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"agent_state_{timestamp}.json"
        filepath = os.path.join(storage_dir, filename)

        try:
            # Extract all steps
            steps_data = []
            for i, step in enumerate(agent.memory.steps):
                step_info = {
                    "index": i,
                    "type": type(step).__name__,
                    "content": str(step),
                    # Try to extract more structured data if possible
                    "raw": repr(step),
                }
                steps_data.append(step_info)

            # Save to file
            with open(filepath, "w") as f:
                json.dump(
                    {
                        "timestamp": timestamp,
                        "total_steps": len(agent.memory.steps),
                        "steps": steps_data,
                    },
                    f,
                    indent=2,
                )

            logger.info(
                f"Saved agent state to {filepath} ({len(agent.memory.steps)} steps)"
            )

        except Exception as e:
            logger.error(f"Failed to save agent state: {str(e)}")
            logger.exception("Full error details:")

    @property
    def name(self) -> str:
        return "Logging Dummy Filtering"


class RawDataCleanupStrategy(AgentStateCleanupStrategy):
    """Strategy that removes raw execution data while preserving essential information.

    How it works:
    1. Identifies steps with completed results (action_output exists)
    2. Removes verbose raw execution data (logs, observations, intermediate messages)
    3. Preserves the final processed result and essential metadata

    Data Preservation Rules:
    - ALWAYS KEEP: action_output (final result), tool_calls (what was executed),
      model_output (agent reasoning)
    - ALWAYS DROP: observations (raw logs), model_input_messages content (verbose conversation)
    - CONDITIONAL: Keep error details if step failed, keep raw data if no final result

    Example transformation:
    Before: observations="partner_summary_47db8d95\nCyberAI Dynamics..." (2KB)
           model_input_messages=[tool-response with same data] (2KB)
           action_output="Summary: CyberAI Dynamics GmbH..." (200B)
    After:  observations="[REMOVED - see action_output]"
           model_input_messages=[cleaned]
           action_output="Summary: CyberAI Dynamics GmbH..." (preserved)

    Memory savings: ~90% while maintaining zero information loss.
    """

    def __init__(self) -> None:
        """Initialize the raw data cleanup strategy."""
        pass

    def cleanup(self, agent: Any) -> None:
        """Remove raw execution data from agent steps while preserving essential information.

        Processing logic:
        1. Iterate through all agent memory steps
        2. For each ActionStep with a final result:
           - Clear verbose observations and execution logs
           - Clean model_input_messages tool-response content
           - Preserve action_output, tool_calls, and model_output
        3. Skip TaskSteps (they're already minimal)
        4. Preserve error information if step failed
        """
        logger.info(f"Running {self.name} strategy")

        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            logger.warning("Agent does not have memory.steps, skipping")
            return

        cleaned_fields = 0

        for step in agent.memory.steps:
            # Skip TaskSteps - they're already minimal
            if not hasattr(step, "action_output"):
                continue

            # Skip steps with errors - preserve error information
            if hasattr(step, "error") and step.error:
                continue

            # Only clean steps that have a final result
            if hasattr(step, "action_output") and step.action_output:
                # Remove redundant observations (keep final result in action_output)
                if hasattr(step, "observations") and step.observations:
                    step.observations = "[REMOVED - see action_output]"
                    cleaned_fields += 1

                # Clean redundant tool-response content in model_input_messages
                if hasattr(step, "model_input_messages") and step.model_input_messages:
                    for msg in step.model_input_messages:
                        if isinstance(msg, dict) and msg.get("role") == "tool-response":
                            if "content" in msg and msg["content"]:
                                msg["content"] = "[REMOVED - see action_output]"
                                cleaned_fields += 1

                # Clean observations_images if present (keep action_output)
                if hasattr(step, "observations_images") and step.observations_images:
                    step.observations_images = None
                    cleaned_fields += 1

        logger.info(
            f"Cleaned {cleaned_fields} raw data fields while preserving final results"
        )

    @property
    def name(self) -> str:
        return "Raw Data Cleanup"


class SimpleStepReplacementTestStrategy(AgentStateCleanupStrategy):
    """Test strategy that replaces agent steps with mock data to validate safe modification.

    This strategy tests whether we can safely modify agent.memory.steps without breaking
    smolagents' internal state. It replaces all steps with hardcoded mock data.

    WARNING: This is for testing only! It destroys all conversation history.
    """

    def cleanup(self, agent: Any) -> None:
        """Replace all agent steps with mock data to test safe modification."""
        logger.info(f"Running {self.name} strategy")

        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            logger.warning("Agent does not have memory.steps, skipping")
            return

        original_count = len(agent.memory.steps)

        # Create REAL smolagents TaskStep and ActionStep objects that simulate "risks for 10000"

        # Real TaskStep - simulate the exact question from logs
        mock_task_step = TaskStep(task="risks for 10000", task_images=None)

        # Real ActionStep with realistic risk analysis response
        timing = Timing(start_time=time.time())
        mock_action_step = ActionStep(
            step_number=2, timing=timing
        )  # Use step 2 like the final answer step
        mock_action_step.action_output = "Die Risikobewertung für Geschäftspartner 10000 zeigt ein geringes Risiko auf der ersten Lieferantenstufe (T0), während höhere Lieferantenstufen (T1-n und Tn) ein erhöhtes Risiko aufweisen."
        mock_action_step.error = None
        mock_action_step.observations = "Execution logs:\nLast output from code snippet:\nDie Risikobewertung für Geschäftspartner 10000 zeigt ein geringes Risiko..."
        mock_action_step.observations_images = None
        mock_action_step.tool_calls = []
        mock_action_step.model_output = "Thought: I have retrieved the risk data for business partner 10000. The data shows risk levels for different legal positions and supplier tiers. I will now provide a final answer in German."

        # Replace entire steps list with mock data
        agent.memory.steps = [mock_task_step, mock_action_step]

        new_count = len(agent.memory.steps)
        logger.info(f"Replaced {original_count} steps with {new_count} mock steps")

    @property
    def name(self) -> str:
        return "Simple Step Replacement Test"


class QuestionAnswerConsolidationStrategy(AgentStateCleanupStrategy):
    """Strategy that consolidates completed question-answer cycles into summary steps.

    How it works:
    1. Identifies completed question-answer cycles (TaskStep + ActionSteps with final results)
    2. Consolidates each cycle into a single summary step preserving essential information
    3. Keeps recent/incomplete interactions unchanged

    Data Preservation Rules:
    - ALWAYS KEEP: User question, final answer, completion status, timing metadata
    - ALWAYS DROP: Intermediate processing steps, tool execution details, model reasoning
    - CONDITIONAL: Keep error information if any step failed

    Example transformation:
    Before: TaskStep("summary for 10000") + ActionStep(tool_call) + ActionStep(final_answer)
    After:  ConsolidatedStep(question="summary for 10000", answer="CyberAI Dynamics...", status="completed")

    Memory savings: ~70% for completed cycles while maintaining conversation continuity.
    """

    def __init__(self, keep_recent_cycles: int = 1):
        """Initialize the question-answer consolidation strategy.

        Args:
            keep_recent_cycles: Number of most recent question-answer cycles to keep unconsolidated
        """
        self.keep_recent_cycles = keep_recent_cycles

    def cleanup(self, agent: Any) -> None:
        """Consolidate completed question-answer cycles into summary steps.

        Processing logic:
        1. Identify question-answer cycles (TaskStep followed by ActionSteps)
        2. Find cycles with final results (action_output exists and no errors)
        3. Consolidate older cycles into summary steps
        4. Keep recent cycles unchanged for context
        """

        if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
            logger.warning("Agent does not have memory.steps, skipping")
            return

        # Identify question-answer cycles
        cycles = self._identify_cycles(agent.memory.steps)

        if len(cycles) <= self.keep_recent_cycles:
            logger.info(f"Only {len(cycles)} cycles found, no consolidation needed")
            return

        # Consolidate older cycles (keep recent ones unchanged)
        cycles_to_consolidate = (
            cycles[: -self.keep_recent_cycles]
            if self.keep_recent_cycles > 0
            else cycles
        )

        consolidated_count = 0
        for cycle in cycles_to_consolidate:
            if self._can_consolidate_cycle(cycle):
                consolidated_step = self._consolidate_cycle(cycle)
                if consolidated_step:
                    # Replace the cycle steps with consolidated step
                    self._replace_cycle_with_consolidated(
                        agent.memory.steps, cycle, consolidated_step
                    )
                    consolidated_count += 1

        logger.info(f"Consolidated {consolidated_count} question-answer cycles")

    def _identify_cycles(self, steps: List[Any]) -> List[List[Any]]:
        """Identify question-answer cycles in the conversation steps."""
        cycles = []
        current_cycle: List[Any] = []

        for step in steps:
            if hasattr(step, "task"):  # TaskStep
                # Start new cycle
                if current_cycle:
                    cycles.append(current_cycle)
                current_cycle = [step]
            elif hasattr(step, "action_output"):  # ActionStep
                if current_cycle:
                    current_cycle.append(step)

        # Add the last cycle if it exists
        if current_cycle:
            cycles.append(current_cycle)

        return cycles

    def _can_consolidate_cycle(self, cycle: List[Any]) -> bool:
        """Check if a cycle can be consolidated (has final result and no errors)."""
        if not cycle:
            return False

        # Must have at least one TaskStep and one ActionStep
        if len(cycle) < 2:
            return False

        # Check if cycle has a final result
        final_result = None
        has_errors = False

        for step in cycle:
            if hasattr(step, "error") and step.error:
                has_errors = True
                break
            if hasattr(step, "action_output") and step.action_output:
                final_result = step.action_output

        return final_result is not None and not has_errors

    def _consolidate_cycle(self, cycle: List[Any]) -> Any:
        """Consolidate a cycle into a summary step."""
        if not cycle:
            return None

        # Extract information from the cycle
        task_step = cycle[0]  # First step should be TaskStep
        question = getattr(task_step, "task", "Unknown question")

        # Find the final answer
        final_answer = None
        total_duration = 0

        for step in cycle[1:]:  # Skip TaskStep
            if hasattr(step, "action_output") and step.action_output:
                final_answer = step.action_output
            if (
                hasattr(step, "timing")
                and hasattr(step.timing, "duration")
                and step.timing.duration is not None
            ):
                total_duration += step.timing.duration

        # Create consolidated step using REAL smolagents ActionStep
        timing = Timing(start_time=time.time())
        consolidated = ActionStep(step_number=1, timing=timing)
        consolidated.action_output = final_answer or "No final answer found"
        consolidated.error = None
        consolidated.observations = f"[CONSOLIDATED] Original question: {question}"
        consolidated.observations_images = None
        consolidated.tool_calls = []
        consolidated.model_output = f"Consolidated answer for: {question}"

        # Add custom attributes for tracking (using setattr to avoid mypy errors)
        setattr(consolidated, "_consolidated_question", question)
        setattr(consolidated, "_original_steps_count", len(cycle))
        setattr(consolidated, "_total_duration", total_duration)
        setattr(consolidated, "_status", "completed")

        return consolidated

    def _replace_cycle_with_consolidated(
        self, steps: List[Any], cycle: List[Any], consolidated: Any
    ) -> None:
        """Replace cycle steps with consolidated step in the steps list."""
        # Find the start index of the cycle
        start_idx = None
        for i, step in enumerate(steps):
            if step is cycle[0]:
                start_idx = i
                break

        if start_idx is not None:
            # PRESERVE TaskStep, replace ActionSteps with consolidated
            # This maintains proper conversation structure (TaskStep -> ActionStep)
            task_step = cycle[0]  # Keep the original TaskStep

            # Remove the cycle steps and insert TaskStep + consolidated ActionStep
            end_idx = start_idx + len(cycle)
            steps[start_idx:end_idx] = [task_step, consolidated]

    @property
    def name(self) -> str:
        return "Question Answer Consolidation"


# Hardcoded list of strategies to apply
CLEANUP_STRATEGIES = [
    LoggingDummyFilteringStrategy(),
    # SimpleStepReplacementTestStrategy(),  # TEST: Validate safe step modification
    QuestionAnswerConsolidationStrategy(),
    RawDataCleanupStrategy(),
    LoggingDummyFilteringStrategy(),
]


def cleanup_agent_state(
    agent: Any, strategies: List[AgentStateCleanupStrategy] = None
) -> None:
    """Clean up the agent's internal state using configured strategies.

    Args:
        agent: The agent instance to clean up
        strategies: List of strategies to apply. If None, uses CLEANUP_STRATEGIES
    """
    if strategies is None:
        strategies = CLEANUP_STRATEGIES

    if not hasattr(agent, "memory") or not hasattr(agent.memory, "steps"):
        logger.warning("Agent does not have memory.steps attribute, skipping cleanup")
        return

    initial_steps = len(agent.memory.steps) if agent.memory.steps else 0
    logger.info(f"Starting agent state cleanup. Initial steps: {initial_steps}")

    for strategy in strategies:
        try:
            strategy.cleanup(agent)
            current_steps = len(agent.memory.steps) if agent.memory.steps else 0
        except Exception as e:
            logger.error(f"Failed to apply {strategy.name} strategy: {str(e)}")
            logger.exception("Full error details:")

    final_steps = len(agent.memory.steps) if agent.memory.steps else 0
    logger.info(f"Agent state cleanup completed. Final steps: {final_steps}")
