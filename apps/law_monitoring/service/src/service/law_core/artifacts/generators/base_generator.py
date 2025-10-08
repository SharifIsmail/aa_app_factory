"""
Base generator class for law summary report generators.

This module provides the abstract base class that all report generators
must implement to ensure a consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from service.law_core.models import LawSummaryData


class BaseReportGenerator(ABC):
    """
    Abstract base class for all law summary report generators.

    This class defines the interface that all report generators must implement.
    Each generator should inherit from this class and implement the render method.
    """

    def __init__(self) -> None:
        """Initialize the generator."""
        pass

    @abstractmethod
    def render(
        self, law_summary_data: LawSummaryData
    ) -> Union[str, bytes, Dict[str, Any]]:
        """
        Render law summary data into the target format.

        Args:
            law_summary_data: Structured law summary analysis data

        Returns:
            Union[str, bytes, Dict[str, Any]]: The rendered report in the target format
            - str for text-based formats (HTML, XML, etc.)
            - bytes for binary formats (PDF, Word, etc.)
            - Dict for structured data formats (JSON, etc.)
        """
        pass
