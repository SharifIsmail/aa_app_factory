from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from smolagents import MultiStepAgent, Tool

from service.agent_core.models import WorkLog


class AgentPersistence(ABC):
    """Abstract base class for agent persistence operations."""

    @abstractmethod
    def get_agent_with_data(
        self, execution_id: str
    ) -> Optional[Tuple[MultiStepAgent, WorkLog, Dict[str, Tool]]]:
        """
        Retrieve agent, its associated work_log, and tools by execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            Tuple of (agent, work_log, tools) if found, None otherwise
        """
        pass

    @abstractmethod
    def store_agent_with_data(
        self,
        execution_id: str,
        agent: MultiStepAgent,
        work_log: WorkLog,
        tools: Dict[str, Tool],
    ) -> None:
        """
        Store agent, its associated work_log, and tools with execution_id as key.

        Args:
            execution_id: The unique identifier for the agent conversation
            agent: The agent instance to store
            work_log: The work_log instance to store
            tools: The tools dictionary to store
        """
        pass

    @abstractmethod
    def exists(self, execution_id: str) -> bool:
        """
        Check if agent conversation exists for execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            True if the agent conversation exists, False otherwise
        """
        pass

    @abstractmethod
    def delete_agent(self, execution_id: str) -> bool:
        """
        Delete agent conversation by execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            True if agent conversation was deleted, False if it didn't exist
        """
        pass


class AgentPersistenceError(Exception):
    """Custom exception for agent persistence operations."""

    pass
