from __future__ import annotations

import PIL.Image  # noqa: F401 # necessary because of ActionStepWithId.model_rebuild() below
from pydantic import BaseModel, ConfigDict
from smolagents import ActionStep


class MultiTurnCounter(BaseModel):
    """Counter for the number of turns of a conversation"""

    count: int = 0


class ExplainabilityExecutionState(BaseModel):
    """State of the execution for explainability generation of one execution_id"""

    multi_turn_counter: MultiTurnCounter = MultiTurnCounter()
    inflight: int = 0


class StepIdentifier(BaseModel):
    """Uniquely identifies a single step in a multi-turn conversation with multiple agents"""

    agent_name: str
    step_number: int
    multi_turn_counter: MultiTurnCounter

    def step_key(self) -> str:
        return f"{self.agent_name}:{self.step_number}"


class ActionStepWithId(BaseModel):
    """ActionStep with unique identifier"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    identity: StepIdentifier
    step: ActionStep


ActionStepWithId.model_rebuild()  # necessary because smolagents has optional image fields


class ExplainedActionStep(BaseModel):
    executed_code: str
    execution_log: str
    code_output: str
    explanation: str
    time_start: float
    time_end: float | None
    agent_name: str
    step_number: int
