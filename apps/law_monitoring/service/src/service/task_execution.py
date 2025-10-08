"""
TaskExecutionManager - Thread-safe singleton for managing task execution.
"""

import atexit
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, List

from loguru import logger

from service.core.utils.singleton import SingletonMeta
from service.law_core.models import TaskStatus, WorkLog


class TaskExecutionManager(metaclass=SingletonMeta):
    """Thread-safe singleton TaskExecutionManager for managing task execution.

    This class manages the execution of background tasks using a thread pool,
    providing task cancellation, monitoring, and cleanup capabilities.
    """

    MAX_WORKERS: int = 50

    def __init__(self) -> None:
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        logger.info("Initializing TaskExecutionManager")
        # Lock for thread-safe operations
        self._lock = threading.RLock()
        # Track active tasks
        self._active_tasks: Dict[str, Future[Any]] = {}
        self._task_threads: Dict[str, threading.Thread] = {}
        # Create thread pool executor
        self._executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        self._initialized = True

        # Register cleanup handler
        atexit.register(self._cleanup_on_exit)

    @classmethod
    def get_instance(cls) -> "TaskExecutionManager":
        """Get the singleton instance. Creates one if it doesn't exist."""
        return cls()

    def execute_task(
        self, execution_id: str, task_function: Callable, *args: Any, **kwargs: Any
    ) -> None:
        """Execute a task in the thread pool.

        Args:
            execution_id: Unique identifier for the task
            task_function: Function to execute
            *args: Arguments to pass to the task function
            **kwargs: Keyword arguments to pass to the task function
        """
        # Submit the task to the executor
        future = self._executor.submit(task_function, *args, **kwargs)

        # Create a thread reference to monitor the future
        thread = threading.Thread(target=lambda: future.result(), daemon=True)
        thread.start()

        # Register the task and thread atomically
        with self._lock:
            self._active_tasks[execution_id] = future
            self._task_threads[execution_id] = thread

        logger.info(f"Task {execution_id} registered with thread ID: {thread.ident}")

    def cancel_task(self, execution_id: str) -> bool:
        """Cancel a running task.

        Args:
            execution_id: The ID of the task to cancel

        Returns:
            True if the task was successfully cancelled, False otherwise
        """
        with self._lock:
            if execution_id not in self._active_tasks:
                return False

            future = self._active_tasks[execution_id]
            thread = self._task_threads.get(execution_id)

        if future and not future.done():
            # Cancel the future
            future.cancel()
            logger.info(f"Future for task {execution_id} cancelled successfully")

            # Attempt to interrupt the thread if possible
            if thread and thread.is_alive():
                logger.info(f"Attempting to terminate thread for task {execution_id}")
                # In Python, there's no clean way to terminate threads forcefully
                # We're marking the status as FAILED so the application logic can
                # check this and exit gracefully

                # Add task to monitor thread termination
                def monitor_thread_termination() -> None:
                    import time

                    max_wait = 60  # Maximum seconds to wait
                    check_interval = 2  # Check every 2 seconds

                    for _ in range(int(max_wait / check_interval)):
                        if not thread.is_alive():
                            logger.info(
                                f"Thread for task {execution_id} successfully terminated"
                            )
                            return
                        time.sleep(check_interval)

                    if thread.is_alive():
                        logger.warning(
                            f"Thread for task {execution_id} is still running after {max_wait} seconds"
                        )

                # Start monitoring in another thread
                monitoring_thread = threading.Thread(
                    target=monitor_thread_termination, daemon=True
                )
                monitoring_thread.start()

            return True
        return False

    def is_active(self, execution_id: str) -> bool:
        """Check if a task is currently active."""
        with self._lock:
            return execution_id in self._active_tasks

    def get_active_tasks_count(self) -> int:
        """Return the number of active tasks."""
        with self._lock:
            return len(self._active_tasks)

    def get_active_task_ids(self) -> List[str]:
        """Return list of active task IDs."""
        with self._lock:
            return list(self._active_tasks.keys())

    def _cleanup_on_exit(self) -> None:
        """Cleanup all running tasks when the application exits."""
        logger.info("Application shutting down, cancelling all running tasks...")

        with self._lock:
            active_task_ids = list(self._active_tasks.keys())

        for execution_id in active_task_ids:
            try:
                with self._lock:
                    future = self._active_tasks.get(execution_id)

                if future and not future.done():
                    logger.info(f"Cancelling task {execution_id} during shutdown")
                    self.cancel_task(execution_id)
            except Exception as e:
                logger.error(
                    f"Error cancelling task {execution_id} during shutdown: {str(e)}"
                )

        # Shutdown the executor
        self._executor.shutdown(wait=False)
        logger.info("All tasks marked for cancellation")


def is_cancelled(work_log: WorkLog, execution_id: str) -> bool:
    """Check if a work log has been cancelled or failed.

    Args:
        work_log: The WorkLog to check
        execution_id: The execution ID for logging purposes

    Returns:
        True if the work log is cancelled or failed, False otherwise
    """
    if work_log.status == TaskStatus.FAILED or work_log.status == TaskStatus.CANCELLED:
        logger.warning(f"Task {execution_id} has been cancelled")
        return True
    return False


# Create a singleton instance to be imported
task_execution_manager = TaskExecutionManager()
