import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from filelock import FileLock, Timeout

from service.agent_core.models import WorkLog

from .agent_persistence import AgentPersistence, AgentPersistenceError

logger = logging.getLogger(__name__)


class InMemoryAgentPersistence(AgentPersistence):
    """In-memory implementation of agent persistence using filelock for thread safety."""

    def __init__(self, lock_timeout: float = 10.0):
        """
        Initialize the in-memory agent persistence.

        Args:
            lock_timeout: Timeout in seconds for acquiring file locks
        """
        # Store tuples of (agent, work_log, tools)
        self._conversations: Dict[str, Tuple[Any, WorkLog, Dict[str, Any]]] = {}
        # Use system temp directory and include process ID for uniqueness
        temp_dir = tempfile.gettempdir()
        pid = os.getpid()
        self._lock_file = os.path.join(temp_dir, f"agent_persistence_{pid}.lock")
        self._lock_timeout = lock_timeout

        # Ensure lock file directory exists
        os.makedirs(os.path.dirname(self._lock_file), exist_ok=True)

    def get_agent_with_data(
        self, execution_id: str
    ) -> Optional[Tuple[Any, WorkLog, Dict[str, Any]]]:
        """
        Retrieve agent, its associated work_log, and tools by execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            Tuple of (agent, work_log, tools) if found, None otherwise

        Raises:
            AgentPersistenceError: If lock timeout occurs
        """
        try:
            with FileLock(self._lock_file, timeout=self._lock_timeout):
                conversation = self._conversations.get(execution_id)
                if conversation:
                    logger.debug(
                        f"Retrieved conversation for execution_id: {execution_id}"
                    )
                else:
                    logger.debug(
                        f"No conversation found for execution_id: {execution_id}"
                    )
                return conversation
        except Timeout:
            error_msg = f"Lock timeout while retrieving conversation for execution_id: {execution_id}"
            logger.error(error_msg)
            raise AgentPersistenceError(error_msg)

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

        Raises:
            AgentPersistenceError: If lock timeout occurs
        """
        try:
            with FileLock(self._lock_file, timeout=self._lock_timeout):
                self._conversations[execution_id] = (agent, work_log, tools)
                logger.debug(f"Stored conversation for execution_id: {execution_id}")
        except Timeout:
            error_msg = f"Lock timeout while storing conversation for execution_id: {execution_id}"
            logger.error(error_msg)
            raise AgentPersistenceError(error_msg)

    def exists(self, execution_id: str) -> bool:
        """
        Check if agent conversation exists for execution_id.

        Args:
            execution_id: The unique identifier for the agent conversation

        Returns:
            True if the agent conversation exists, False otherwise

        Raises:
            AgentPersistenceError: If lock timeout occurs
        """
        try:
            with FileLock(self._lock_file, timeout=self._lock_timeout):
                exists = execution_id in self._conversations
                logger.debug(
                    f"Conversation exists check for execution_id {execution_id}: {exists}"
                )
                return exists
        except Timeout:
            error_msg = f"Lock timeout while checking existence for execution_id: {execution_id}"
            logger.error(error_msg)
            raise AgentPersistenceError(error_msg)

    def _delete_agent_unsafe(self, execution_id: str) -> bool:
        """Delete agent without acquiring lock (assumes lock is already held)."""
        if execution_id in self._conversations:
            del self._conversations[execution_id]
            logger.debug(f"Deleted conversation for execution_id: {execution_id}")
            return True
        else:
            logger.debug(f"No conversation to delete for execution_id: {execution_id}")
            return False

    def delete_agent(self, execution_id: str) -> bool:
        """Delete agent conversation by execution_id."""
        try:
            with FileLock(self._lock_file, timeout=self._lock_timeout):
                return self._delete_agent_unsafe(execution_id)
        except Timeout:
            error_msg = f"Lock timeout while deleting conversation for execution_id: {execution_id}"
            logger.error(error_msg)
            raise AgentPersistenceError(error_msg)

    def purge_expired(self) -> int:
        """Remove all expired conversations. Returns number of deleted entries."""
        removed = 0
        try:
            with FileLock(self._lock_file, timeout=self._lock_timeout):
                now = datetime.now()
                for execution_id, (_, work_log, _) in list(self._conversations.items()):
                    try:
                        if work_log.expires_at and work_log.expires_at < now:
                            if self._delete_agent_unsafe(execution_id):
                                removed += 1
                    except Exception:
                        continue
        except Timeout:
            error_msg = "Lock timeout while purging expired conversations"
            logger.error(error_msg)
            raise AgentPersistenceError(error_msg)
        return removed
