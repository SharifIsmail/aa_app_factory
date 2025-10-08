import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from loguru import logger

from service.law_core.background_work.workers_constants import (
    DATA_FOLDER,
    EXECUTION_LOG_FILE,
    WORKER_RUN_TIMEOUT_MINUTES,
)
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.metrics import (
    worker_active_runs,
    worker_executions_total,
    worker_last_run_timestamp,
    worker_run_duration_seconds,
    worker_runs_total,
)


class WorkerStatus(Enum):
    """Enum for worker run statuses."""

    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkerExitReason(Enum):
    """
    Enum for worker exit reasons to prevent Prometheus label cardinality explosion.
    IMPORTANT: These values are used as Prometheus metric labels. Adding new values or
    allowing arbitrary strings could lead to high label cardinality.

    When adding new exit reasons:
    1. Only add them if they represent a fundamentally different category of exit
    2. Keep the total number of enum values small (ideally < 10)
    3. Use descriptive but concise names
    4. Never use dynamic/user-generated content as exit reasons

    For any specific error details, use logging instead of metric labels.
    """

    NONE = "none"  # No specific exit reason (successful execution)
    ANOTHER_INSTANCE_RUNNING = "another_instance_running"  # Worker already active
    TIMEOUT = "timeout"  # Worker timed out or was considered stale
    ERROR = "error"  # General error category for any failures


class BaseWorker(ABC):
    """Base class for all background workers."""

    # Timeout in minutes (if run is older than this, consider it failed)
    RUN_TIMEOUT_MINUTES = WORKER_RUN_TIMEOUT_MINUTES

    def __init__(self, worker_type: str) -> None:
        """
        Initialize the base worker.

        Args:
            worker_type: Type identifier for this worker (e.g., "discovery", "processing")
        """
        self.worker_uuid = str(uuid.uuid4())
        self.worker_type = worker_type
        self.runs_file = f"{worker_type}_runs.json"
        self._ensure_folders_exist()

    def _ensure_folders_exist(self) -> None:
        """Ensure required folders exist in storage."""
        storage_backend = get_configured_storage_backend()
        storage_backend.create_folder(DATA_FOLDER)

    @staticmethod
    def _safe_exit_reason(reason: Optional[str]) -> WorkerExitReason:
        """
        Convert string reasons to safe enum values to prevent Prometheus label high cardinality.
        """
        if not reason:
            return WorkerExitReason.NONE

        reason_lower = reason.lower()

        if "another" in reason_lower and "running" in reason_lower:
            return WorkerExitReason.ANOTHER_INSTANCE_RUNNING
        elif "timeout" in reason_lower:
            return WorkerExitReason.TIMEOUT
        elif "error" in reason_lower or "fail" in reason_lower:
            return WorkerExitReason.ERROR
        else:
            # Default to ERROR for any unrecognized reason to prevent new labels
            return WorkerExitReason.ERROR

    @abstractmethod
    def _do_work(self) -> dict:
        """
        Perform the actual work. Implemented by subclasses.

        Returns:
            Dictionary with work results that will be added to the run record
        """
        pass

    def _log_execution_attempt(
        self,
        start_time: datetime,
        work_started: bool,
        exit_reason: Optional[WorkerExitReason] = None,
    ) -> None:
        """
        Log every execution attempt to the common execution log.

        Args:
            start_time: When the run method was invoked
            work_started: Whether _do_work was actually started
            exit_reason: Reason for not starting work (if work_started is False).
                        Must be a WorkerExitReason enum value to prevent Prometheus
                        label cardinality explosion.
        """
        # Validate and constrain exit_reason to prevent label cardinality explosion
        exit_reason_value = (
            exit_reason.value if exit_reason else WorkerExitReason.NONE.value
        )

        execution_record = {
            "execution_uuid": str(uuid.uuid4()),
            "worker_uuid": self.worker_uuid,
            "worker_type": self.worker_type,
            "invoked_at": start_time.isoformat(),
            "work_started": work_started,
            "exit_reason": exit_reason_value,
        }

        # Load existing executions
        executions = self._load_executions()
        executions.append(execution_record)
        self._save_executions(executions)

        # Update metrics - using constrained enum values prevents label cardinality explosion
        worker_executions_total.labels(
            worker_type=self.worker_type,
            work_started=str(work_started),
            exit_reason=exit_reason_value,
        ).inc()

        logger.debug(
            f"{self.worker_type} worker: logged execution attempt - work_started={work_started}, exit_reason={exit_reason_value}"
        )

    def _load_executions(self) -> list[dict]:
        """Load all execution records from the common execution log."""
        storage_backend = get_configured_storage_backend()
        content = storage_backend.load_file(DATA_FOLDER, EXECUTION_LOG_FILE)
        if content:
            try:
                return json.loads(content)
            except Exception as e:
                logger.warning(f"Failed to parse execution log file: {e}")
        return []

    def _save_executions(self, executions: list[dict]) -> None:
        """Save all execution records to the common execution log."""
        content = json.dumps(executions, indent=2)
        storage_backend = get_configured_storage_backend()
        storage_backend.save_file(DATA_FOLDER, EXECUTION_LOG_FILE, content)

    def run(self) -> None:
        """
        Run the worker with simple active worker checking.

        The worker will exit if another instance is already running.
        """
        logger.info(f"{self.worker_type} worker: starting")
        start_time = datetime.now()

        # Check if we can start (no other active workers)
        if not self._can_start_new_run(start_time):
            # Log execution attempt that didn't start work
            self._log_execution_attempt(
                start_time,
                work_started=False,
                exit_reason=WorkerExitReason.ANOTHER_INSTANCE_RUNNING,
            )
            logger.info(
                f"{self.worker_type} worker: another instance is already running, exiting"
            )
            return

        # Log execution attempt that will start work
        self._log_execution_attempt(start_time, work_started=True)

        # Update active runs metric
        worker_active_runs.labels(worker_type=self.worker_type).inc()

        # Create run record
        run_record: dict[str, Any] = {
            "uuid": self.worker_uuid,
            "worker_type": self.worker_type,
            "status": WorkerStatus.STARTED.value,
            "start_time": start_time.isoformat(),
            "end_time": None,
            "errors": [],
        }
        self._add_run_record(run_record)

        try:
            # Perform the actual work
            work_results = self._do_work()

            # Update run record to completed
            end_time = datetime.now()
            run_record.update(
                {
                    "status": WorkerStatus.COMPLETED.value,
                    "end_time": end_time.isoformat(),
                    **work_results,
                }
            )
            self._update_run_record(run_record)

            # Update metrics for successful completion
            self._update_completion_metrics(
                start_time, end_time, WorkerStatus.COMPLETED
            )

            logger.info(f"{self.worker_type} worker: completed successfully")

        except Exception as e:
            error_msg = f"{self.worker_type} worker failed: {str(e)}"
            logger.error(error_msg)

            # Update run record to failed
            end_time = datetime.now()
            run_record.update(
                {
                    "status": WorkerStatus.FAILED.value,
                    "end_time": end_time.isoformat(),
                    "errors": [error_msg],
                }
            )
            self._update_run_record(run_record)

            # Update metrics for failure
            self._update_completion_metrics(start_time, end_time, WorkerStatus.FAILED)

        finally:
            # Always decrement active runs
            worker_active_runs.labels(worker_type=self.worker_type).dec()

    def _update_completion_metrics(
        self, start_time: datetime, end_time: datetime, status: WorkerStatus
    ) -> None:
        """Update Prometheus metrics after worker completion."""
        duration = (end_time - start_time).total_seconds()

        # Update counters and histograms
        worker_runs_total.labels(
            worker_type=self.worker_type, status=status.value
        ).inc()
        worker_run_duration_seconds.labels(
            worker_type=self.worker_type, status=status.value
        ).observe(duration)
        worker_last_run_timestamp.labels(
            worker_type=self.worker_type, status=status.value
        ).set(end_time.timestamp())

    def _can_start_new_run(self, start_time: datetime) -> bool:
        """
        Check if a new run can be started.

        Args:
            start_time: When this worker started

        Returns:
            True if new run can start, False if another is active
        """
        runs = self._load_runs()

        # Check for any active (STARTED) runs
        for run in runs:
            if run["status"] == WorkerStatus.STARTED.value:
                run_start = datetime.fromisoformat(run["start_time"])
                age_minutes = (start_time - run_start).total_seconds() / 60

                if age_minutes < self.RUN_TIMEOUT_MINUTES:
                    logger.info(
                        f"{self.worker_type} worker: active run {run['uuid']} is {age_minutes:.1f} minutes old"
                    )
                    return False
                else:
                    # Mark stale run as failed
                    logger.warning(
                        f"{self.worker_type} worker: marking stale run {run['uuid']} as failed ({age_minutes:.1f} minutes old)"
                    )
                    run["status"] = WorkerStatus.FAILED.value
                    run["end_time"] = start_time.isoformat()
                    run["errors"] = run.get("errors", []) + [
                        "Run timeout - marked as failed by new worker"
                    ]
                    self._save_runs(runs)

        return True

    def _add_run_record(self, run_record: dict) -> None:
        """Add a new run record to the runs file."""
        runs = self._load_runs()
        runs.append(run_record)
        self._save_runs(runs)

    def _update_run_record(self, updated_record: dict) -> None:
        """Update an existing run record."""
        runs = self._load_runs()
        for i, run in enumerate(runs):
            if run["uuid"] == self.worker_uuid:
                runs[i] = updated_record
                break
        self._save_runs(runs)

    def _load_runs(self) -> list[dict]:
        """Load all runs for this worker type."""
        storage_backend = get_configured_storage_backend()
        content = storage_backend.load_file(DATA_FOLDER, self.runs_file)
        if content:
            try:
                return json.loads(content)
            except Exception as e:
                logger.warning(
                    f"{self.worker_type} worker: failed to parse runs file: {e}"
                )
        return []

    def _save_runs(self, runs: list[dict]) -> None:
        """Save all runs for this worker type."""
        content = json.dumps(runs, indent=2)
        storage_backend = get_configured_storage_backend()
        storage_backend.save_file(DATA_FOLDER, self.runs_file, content)

    def get_runs(self) -> list[dict]:
        """Get all runs for this worker type."""
        return self._load_runs()

    def get_active_runs(self) -> list[dict]:
        """Get all currently active (STARTED) runs."""
        runs = self._load_runs()
        return [run for run in runs if run["status"] == WorkerStatus.STARTED.value]

    def get_recent_runs(self, limit: int = 10) -> list[dict]:
        """
        Get recent runs, sorted by start time (most recent first).

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of recent run records
        """
        runs = self._load_runs()
        # Sort by start_time descending
        sorted_runs = sorted(runs, key=lambda x: x["start_time"], reverse=True)
        return sorted_runs[:limit]

    @classmethod
    def get_all_executions(cls, limit: Optional[int] = None) -> list[dict]:
        """
        Get all execution records from all workers, sorted by invoked_at desc.

        Args:
            limit: Maximum number of records to return (optional)

        Returns:
            List of execution records
        """
        storage_backend = get_configured_storage_backend()
        content = storage_backend.load_file(DATA_FOLDER, EXECUTION_LOG_FILE)
        if content:
            try:
                executions = json.loads(content)
                # Sort by invoked_at descending (most recent first)
                sorted_executions = sorted(
                    executions, key=lambda x: x["invoked_at"], reverse=True
                )
                return sorted_executions[:limit] if limit else sorted_executions
            except Exception as e:
                logger.warning(f"Failed to parse execution log file: {e}")
        return []

    @classmethod
    def get_executions_by_worker_type(
        cls, worker_type: str, limit: Optional[int] = None
    ) -> list[dict]:
        """
        Get execution records for a specific worker type.

        Args:
            worker_type: The worker type to filter by
            limit: Maximum number of executions to return (most recent first)

        Returns:
            List of execution records for the specified worker type
        """
        all_executions = cls.get_all_executions()
        filtered_executions = [
            exec for exec in all_executions if exec["worker_type"] == worker_type
        ]
        return filtered_executions[:limit] if limit else filtered_executions
