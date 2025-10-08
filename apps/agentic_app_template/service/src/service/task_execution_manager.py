import atexit
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


class TaskExecutionManager:
    _instance: Optional["TaskExecutionManager"] = None
    MAX_WORKERS: int = 50

    def __new__(cls) -> "TaskExecutionManager":
        if cls._instance is None:
            logger.info("Creating TaskExecutionManager singleton instance")
            cls._instance = super(TaskExecutionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self, "_initialized", False):
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
        if cls._instance is None:
            cls._instance = TaskExecutionManager()
        return cls._instance

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

        # Register the task and thread
        self._active_tasks[execution_id] = future
        self._task_threads[execution_id] = thread
        logger.info(f"Task {execution_id} registered with thread ID: {thread.ident}")

    def cancel_task(self, execution_id: str) -> bool:
        if execution_id in self._active_tasks:
            future = self._active_tasks[execution_id]
            thread = self._task_threads.get(execution_id)

            if future and not future.done():
                # Cancel the future
                future.cancel()
                logger.info(f"Future for task {execution_id} cancelled successfully")

                # Attempt to interrupt the thread if possible
                if thread and thread.is_alive():
                    logger.info(
                        f"Attempting to terminate thread for task {execution_id}"
                    )
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
        return execution_id in self._active_tasks

    def get_active_tasks_count(self) -> int:
        """Return the number of active tasks."""
        return len(self._active_tasks)

    def get_active_task_ids(self) -> List[str]:
        """Return list of active task IDs."""
        return list(self._active_tasks.keys())

    def _cleanup_on_exit(self) -> None:
        """Cleanup all running tasks when the application exits."""
        logger.info("Application shutting down, cancelling all running tasks...")
        for execution_id in list(self._active_tasks.keys()):
            try:
                if (
                    self._active_tasks[execution_id]
                    and not self._active_tasks[execution_id].done()
                ):
                    logger.info(f"Cancelling task {execution_id} during shutdown")
                    self.cancel_task(execution_id)
            except Exception as e:
                logger.error(
                    f"Error cancelling task {execution_id} during shutdown: {str(e)}"
                )

        # Shutdown the executor
        self._executor.shutdown(wait=False)
        logger.info("All tasks marked for cancellation")
