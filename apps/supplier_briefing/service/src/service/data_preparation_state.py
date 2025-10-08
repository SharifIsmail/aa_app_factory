from enum import Enum
from functools import lru_cache

from pydantic import BaseModel


class DataPreparationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DataPreparationState(BaseModel):
    status: DataPreparationStatus = DataPreparationStatus.PENDING
    error: str | None = None


class DataPreparationStateManager:
    _state: DataPreparationState

    def __init__(self) -> None:
        self._state = DataPreparationState()

    def get_state(self) -> DataPreparationState:
        return self._state.model_copy()

    def set_pending(self) -> None:
        self._state = DataPreparationState(status=DataPreparationStatus.PENDING)

    def set_in_progress(self) -> None:
        self._state = DataPreparationState(status=DataPreparationStatus.IN_PROGRESS)

    def set_completed(self) -> None:
        self._state = DataPreparationState(status=DataPreparationStatus.COMPLETED)

    def set_failed(self, error: str) -> None:
        self._state = DataPreparationState(
            status=DataPreparationStatus.FAILED, error=error
        )


@lru_cache(maxsize=1)
def with_data_preperation_state() -> DataPreparationStateManager:
    return DataPreparationStateManager()
