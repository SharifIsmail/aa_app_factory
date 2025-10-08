from __future__ import annotations

import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Deque, Dict, Optional

from loguru import logger
from smolagents import ActionStep, CodeAgent

from service.agent_core.explainability.explainability_client import (
    ExplainabilityLLMClient,
)
from service.agent_core.explainability.explainability_processor import (
    ExplainabilityProcessor,
)
from service.agent_core.explainability.models import (
    ActionStepWithId,
    ExplainabilityExecutionState,
    ExplainedActionStep,
    StepIdentifier,
)
from service.agent_core.models import TaskStatus, WorkLog
from service.agent_core.work_log_manager import TaskKeys, update_task_status


class ExplainabilityService:
    """Singleton service to handle explainability across all executions.

    Responsibilities per execution_id:
    - Maintain a queue of MemorySteps (ActionSteps) to be processed
    - Process steps asynchronously with up to 3 concurrent workers
    - Persist results to WorkLog repositories
    - Clear the in-memory queue when all steps are processed
    """

    _instance: Optional["ExplainabilityService"] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_single_instance(cls) -> "ExplainabilityService":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = ExplainabilityService()
        return cls._instance

    def __init__(self) -> None:
        # Attributes per execution_id
        self._queues: Dict[str, Deque[ActionStepWithId]] = {}
        self._locks: Dict[str, threading.RLock] = {}
        self._executors: Dict[str, ThreadPoolExecutor] = {}
        self._work_logs: Dict[str, WorkLog] = {}
        self._states: Dict[str, ExplainabilityExecutionState] = {}
        self._enabled: bool = True

        # Processor (stateless; shared)
        self._processor = ExplainabilityProcessor(ExplainabilityLLMClient())

        # Constants
        self._max_workers_per_execution = 3
        self._max_retries = 3
        self._explained_steps_key = "explained_steps"

    # Registration
    def register_work_log(self, execution_id: str, work_log: WorkLog) -> None:
        with self._get_lock(execution_id):
            self._work_logs[execution_id] = work_log
            if execution_id not in self._queues:
                self._queues[execution_id] = deque()
            if execution_id not in self._executors:
                self._executors[execution_id] = ThreadPoolExecutor(
                    max_workers=self._max_workers_per_execution,
                    thread_name_prefix=f"explainability_{execution_id}",
                )
            if execution_id not in self._states:
                self._states[execution_id] = ExplainabilityExecutionState()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def make_callback(
        self, execution_id: str
    ) -> Callable[[ActionStep, CodeAgent], None]:
        """Returns callback for agents to generate explainability after each MemoryStep"""

        def on_step(memory_step: ActionStep, agent: CodeAgent) -> None:
            work_log = self._get_worklog(execution_id)
            if not self._enabled:
                return
            # Only process successful ActionSteps
            if not isinstance(memory_step, ActionStep):
                return
            if getattr(memory_step, "error", None) is not None:
                return
            try:
                update_task_status(
                    work_log, TaskKeys.GENERATE_EXPLAINABILITY, TaskStatus.IN_PROGRESS
                )
                step_number = int(memory_step.step_number)
                state = self._get_explainability_execution_state(execution_id)
                identity = StepIdentifier(
                    agent_name=agent.name
                    if agent.name is not None
                    else "unnamed_agent",
                    step_number=step_number,
                    multi_turn_counter=state.multi_turn_counter,
                )
                envelope = ActionStepWithId(identity=identity, step=memory_step)
                self.queue_memory_step(execution_id, envelope)
            except Exception:
                logger.exception("Failed to push memory step to explainability queue")

        return on_step

    def queue_memory_step(self, execution_id: str, envelope: ActionStepWithId) -> None:
        """Queue a step for background explainability processing."""
        if not self._enabled:
            return
        with self._get_lock(execution_id):
            self._get_worklog(execution_id)
            self._get_explainability_execution_state(execution_id)
            self._queues[execution_id].append(envelope)
            self._schedule_workers_if_needed(execution_id)

    # Internal scheduling
    def _schedule_workers_if_needed(self, execution_id: str) -> None:
        with self._get_lock(execution_id):
            queue = self._queues[execution_id]
            explainability_execution_state = self._get_explainability_execution_state(
                execution_id
            )
            capacity = (
                self._max_workers_per_execution
                - explainability_execution_state.inflight
            )
            while capacity > 0 and len(queue) > 0:
                explainability_execution_state.inflight += 1
                capacity -= 1
                self._executors[execution_id].submit(
                    self._deque_and_process_single_action_step, execution_id
                )

            if len(queue) == 0 and explainability_execution_state.inflight == 0:
                work_log = self._get_worklog(execution_id)
                update_task_status(
                    work_log, TaskKeys.GENERATE_EXPLAINABILITY, TaskStatus.COMPLETED
                )

    def _deque_and_process_single_action_step(self, execution_id: str) -> None:
        action_step_with_id: ActionStepWithId | None = None
        try:
            with self._get_lock(execution_id):
                if len(self._queues[execution_id]) == 0:
                    return
                action_step_with_id = self._queues[execution_id].popleft()

            if action_step_with_id is None:
                return

            identity = action_step_with_id.identity
            action_step = action_step_with_id.step
            action_step_key = identity.step_key()

            # Retry up to _max_retries
            attempts = 0
            while attempts < self._max_retries:
                attempts += 1
                try:
                    work_log = self._get_worklog(execution_id)
                    state = self._get_explainability_execution_state(execution_id)
                    # Skip outdated action_steps
                    if (
                        identity.multi_turn_counter.count
                        != state.multi_turn_counter.count
                    ):
                        logger.info(
                            f"Skipping outdated explainability action_step for {action_step_key} (multi turn counter mismatch)"
                        )
                        break
                    explained_action = (
                        self._processor.explain_single_action_step_if_possible(
                            action_step,
                            work_log.tool_logs,
                            agent_name=identity.agent_name,
                        )
                    )

                    if explained_action is not None:
                        self._store_explained_action_step_in_worklog(
                            execution_id, explained_action
                        )
                    # Whether we had explanation or not, we consider this action_step processed
                    break
                except Exception as e:
                    if attempts >= self._max_retries:
                        logger.error(
                            f"Explainability failed for {action_step_key} after {attempts} attempts: {e}"
                        )
                    else:
                        logger.warning(
                            f"Explainability attempt {attempts} failed for {action_step_key}: {e}"
                        )
        finally:
            with self._get_lock(execution_id):
                state = self._get_explainability_execution_state(execution_id)
                state.inflight = max(0, state.inflight - 1)
                # Continue draining if items remain
                self._schedule_workers_if_needed(execution_id)

    def _store_explained_action_step_in_worklog(
        self, execution_id: str, action: ExplainedActionStep
    ) -> None:
        with self._get_lock(execution_id):
            work_log = self._get_worklog(execution_id)
            work_log.explained_steps.append(action)
            work_log.explained_steps.sort(key=lambda x: x.time_start)

    def advance_multi_turn_counter(self, execution_id: str) -> None:
        """Advance multi turn counter to prevent stale writes."""
        if not self._enabled:
            return
        with self._get_lock(execution_id):
            state = self._get_explainability_execution_state(execution_id)
            # Advance multi turn counter so any in-flight tasks from previous turn do not persist
            state.multi_turn_counter.count += 1

    # Helpers
    def _get_lock(self, execution_id: str) -> threading.RLock:
        if execution_id not in self._locks:
            self._locks[execution_id] = threading.RLock()
        return self._locks[execution_id]

    def _get_worklog(self, execution_id: str) -> WorkLog:
        work_log = self._work_logs.get(execution_id)
        if work_log is None:
            raise RuntimeError(
                f"WorkLog not registered for execution_id={execution_id}. Call register_work_log first."
            )
        return work_log

    def _get_explainability_execution_state(
        self, execution_id: str
    ) -> ExplainabilityExecutionState:
        state = self._states.get(execution_id)
        if state is None:
            state = ExplainabilityExecutionState()
            self._states[execution_id] = state
        return state
