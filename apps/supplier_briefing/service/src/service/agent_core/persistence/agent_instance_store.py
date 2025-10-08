import logging
from typing import Any, Dict, Optional, Tuple

from service.agent_core.models import WorkLog
from service.core.utils.singleton import SingletonMeta

from .agent_persistence import AgentPersistence
from .in_memory_agent_persistence import InMemoryAgentPersistence

logger = logging.getLogger(__name__)


class AgentInstanceStore(metaclass=SingletonMeta):
    """
    Singleton store for managing agent instances.

    This class provides a centralized interface for storing and retrieving
    agent instances, using pluggable persistence implementations.
    """

    def __init__(self, persistence: Optional[AgentPersistence] = None):
        """
        Initialize the AgentInstanceStore singleton.

        Args:
            persistence: Optional persistence implementation.
                        Defaults to InMemoryAgentPersistence if not provided.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        self._persistence = persistence or InMemoryAgentPersistence()
        self._initialized = True

        logger.info(
            f"AgentInstanceStore initialized with persistence: {type(self._persistence).__name__}"
        )

    def get_agent_with_data(
        self, execution_id: str
    ) -> Optional[Tuple[Any, WorkLog, Dict[str, Any]]]:
        """
        Retrieve agent, its associated work_log, and tools by execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            Tuple of (agent, work_log, tools) if found, None otherwise
        """
        logger.debug(f"Getting agent with data for execution_id: {execution_id}")
        return self._persistence.get_agent_with_data(execution_id)

    def store_agent_with_data(
        self, execution_id: str, agent: Any, work_log: WorkLog, tools: Dict[str, Any]
    ) -> None:
        """
        Store agent, its associated work_log, and tools with execution_id as key.

        Args:
            execution_id: The unique identifier for the agent conversation
            agent: The agent instance to store
            work_log: The work_log instance to store
            tools: The tools dictionary to store
        """
        logger.debug(f"Storing agent with data for execution_id: {execution_id}")
        self._persistence.store_agent_with_data(execution_id, agent, work_log, tools)

    def exists(self, execution_id: str) -> bool:
        """
        Check if agent conversation exists for execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            True if the agent conversation exists, False otherwise
        """
        logger.debug(f"Checking if agent exists for execution_id: {execution_id}")
        return self._persistence.exists(execution_id)

    def delete_agent(self, execution_id: str) -> bool:
        """
        Delete agent conversation by execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            True if agent conversation was deleted, False if it didn't exist
        """
        sanitized_execution_id = execution_id.replace("\r", "").replace("\n", "")
        logger.debug(f"Deleting agent for execution_id: {sanitized_execution_id}")
        return self._persistence.delete_agent(execution_id)

    def purge_expired(self) -> int:
        """Purge all expired agent conversations. Returns the number removed."""
        purge_fn = getattr(self._persistence, "purge_expired", None)
        if callable(purge_fn):
            return purge_fn()
        return 0


# Create a singleton instance to be imported
agent_instance_store = AgentInstanceStore()
