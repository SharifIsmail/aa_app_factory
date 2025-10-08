"""Base class for quick action data fetchers."""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T_Response = TypeVar("T_Response")
T_FilterParams = TypeVar("T_FilterParams", bound=BaseModel)


class QuickActionResponse(GenericModel, Generic[T_Response]):
    """Generic response model for all quick action data fetchers."""

    success: bool
    data: List[T_Response]
    error: Optional[str] = None


class BaseQuickActionDataFetcher(ABC, Generic[T_Response, T_FilterParams]):
    """Abstract base class for quick action data fetchers.

    Retrieves data for display in the UI before a quick action is triggered.
    """

    @abstractmethod
    def fetch_data(
        self, filter_params: T_FilterParams
    ) -> QuickActionResponse[T_Response]:
        """
        Fetch and filter data based on the provided parameters.

        This method is designed to handle exceptions during its execution and report
        failures through the `success` and `error` fields of the returned
        `QuickActionResponse` object. It should not raise exceptions for expected
        errors (e.g., data not found, validation errors).

        Args:
            filter_params: A discriminated union of quick action filter parameters.

        Returns:
            A `QuickActionResponse` object.
            - If successful, `success` is True, `data` contains the fetched items,
              and `error` is None.
            - If an error occurs, `success` is False, `data` is an empty list,
              and `error` contains a descriptive message.

        Raises:
            Exception: This method should only raise exceptions for unrecoverable
                or unexpected errors that cannot be handled gracefully and
                reported in the `QuickActionResponse`.
        """
        pass

    @abstractmethod
    def validate_filter_params(self, filter_params: T_FilterParams) -> None:
        """
        Validate filter parameters specific to this quick action.

        Args:
            filter_params: Parameters to validate

        Raises:
            ValueError: If parameters are invalid
        """
        pass
