import threading
import traceback
import uuid
from datetime import datetime, timedelta, timezone

from loguru import logger

from service.dependencies import with_settings
from service.law_core.background_work.database_sync_worker import DatabaseSyncWorker
from service.law_core.background_work.discovery_worker import DiscoveryWorker
from service.law_core.background_work.evaluation_worker import EvaluationWorker
from service.law_core.background_work.reconciliation_worker import ReconciliationWorker
from service.law_core.background_work.summary_worker import SummaryWorker
from service.law_core.background_work.workers_constants import (
    DATABASE_SYNC_SCHEDULED_HOUR_UTC,
    DISCOVERY_LOOP_INTERVAL_SECONDS,
    ERROR_RETRY_WAIT_SECONDS,
    ERROR_RETRY_WAIT_SHORT_SECONDS,
    EVALUATION_SNAPSHOT_SCHEDULED_HOUR_UTC,
    PROCESSING_LOOP_INTERVAL_SECONDS,
    RECONCILIATION_INTERVAL_HOURS,
)
from service.law_core.persistence.storage_backend import StorageBackendType
from service.task_execution import task_execution_manager

# Global shutdown event for graceful termination
shutdown_event = threading.Event()


def discovery_loop() -> None:
    """Discovery loop - runs every hour."""
    logger.info("Discovery loop started")

    while not shutdown_event.is_set():
        try:
            logger.info("Discovery loop: spawning worker")
            spawn_discovery_worker()
            logger.info(
                f"Discovery loop: sleeping for {DISCOVERY_LOOP_INTERVAL_SECONDS} seconds"
            )
            shutdown_event.wait(DISCOVERY_LOOP_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Error in discovery loop: {e}")
            if not shutdown_event.wait(ERROR_RETRY_WAIT_SECONDS):
                continue
    logger.info("Discovery loop stopped")


def processing_loop() -> None:
    """Simple processing loop - runs forever."""
    logger.info("Processing loop started")

    while not shutdown_event.is_set():
        try:
            logger.info("Processing loop: spawning worker")
            spawn_processing_worker()
            logger.info(
                f"Processing loop: sleeping for {PROCESSING_LOOP_INTERVAL_SECONDS} seconds"
            )
            shutdown_event.wait(PROCESSING_LOOP_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Error in processing loop: {e}")
            if not shutdown_event.wait(ERROR_RETRY_WAIT_SHORT_SECONDS):
                continue
    logger.info("Processing loop stopped")


def reconciliation_loop() -> None:
    """Reconciliation loop - runs every 12 hours."""
    logger.info("Reconciliation loop started")

    while not shutdown_event.is_set():
        try:
            shutdown_event.wait(
                300
            )  # wait 5 minutes before first reconciliation run, to allow discovery worker to discover first
            logger.info("Reconciliation loop: spawning worker")
            spawn_reconciliation_worker()
            logger.info(
                f"Reconciliation loop: sleeping for {RECONCILIATION_INTERVAL_HOURS} hours"
            )
            # Convert hours to seconds for the wait
            shutdown_event.wait(RECONCILIATION_INTERVAL_HOURS * 3600)
        except Exception as e:
            logger.error(f"Error in reconciliation loop: {e}")
            if not shutdown_event.wait(
                ERROR_RETRY_WAIT_SECONDS
            ):  # Wait 5 minutes on error
                continue
    logger.info("Reconciliation loop stopped")


def database_sync_loop() -> None:
    """Database sync loop - runs daily at 3 AM UTC."""
    logger.info("Database Sync loop started - scheduled for daily runs at 3 AM UTC")

    while not shutdown_event.is_set():
        try:
            wait_seconds = _calculate_seconds_until_next_pharia_data_sqlite_sync()

            logger.info(
                f"Sync loop: waiting {wait_seconds} seconds until next 3 AM UTC sync"
            )

            if shutdown_event.wait(wait_seconds):
                break

            logger.info("Sync loop: spawning sync worker at scheduled time")
            spawn_database_sync_worker()

            if not shutdown_event.wait(60):  # Wait 1 minute before next calculation
                continue

        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
            if not shutdown_event.wait(
                ERROR_RETRY_WAIT_SHORT_SECONDS
            ):  # Wait 1 minute on error
                continue
    logger.info("Sync loop stopped")


def evaluation_snapshot_loop() -> None:
    """Evaluation snapshot loop - runs daily at configured UTC hour."""
    logger.info(
        "Evaluation snapshot loop started - scheduled for daily runs at %d AM UTC",
        EVALUATION_SNAPSHOT_SCHEDULED_HOUR_UTC,
    )

    while not shutdown_event.is_set():
        try:
            wait_seconds = _calculate_seconds_until_next_hour(
                EVALUATION_SNAPSHOT_SCHEDULED_HOUR_UTC
            )
            logger.info(
                f"Evaluation snapshot loop: waiting {wait_seconds} seconds until next run"
            )
            if shutdown_event.wait(wait_seconds):
                break

            logger.info("Evaluation snapshot loop: spawning evaluation worker")
            spawn_evaluation_worker()

            if not shutdown_event.wait(60):
                continue
        except Exception as e:
            logger.error(f"Error in evaluation snapshot loop: {e}")
            if not shutdown_event.wait(ERROR_RETRY_WAIT_SHORT_SECONDS):
                continue
    logger.info("Evaluation snapshot loop stopped")


def _calculate_seconds_until_next_pharia_data_sqlite_sync() -> int:
    """
    Calculate the number of seconds until the next 3 AM UTC.

    Returns:
        Number of seconds to wait until next sync time
    """
    now_utc = datetime.now(timezone.utc)

    # Create datetime for today at 3 AM UTC
    today_3am = now_utc.replace(
        hour=DATABASE_SYNC_SCHEDULED_HOUR_UTC, minute=0, second=0, microsecond=0
    )

    if now_utc >= today_3am:
        next_sync = today_3am + timedelta(days=1)
    else:
        next_sync = today_3am

    wait_seconds = int((next_sync - now_utc).total_seconds())

    logger.debug(
        f"Current time: {now_utc}, Next sync: {next_sync}, Wait: {wait_seconds}s"
    )

    return wait_seconds


def _calculate_seconds_until_next_hour(hour_utc: int) -> int:
    """Calculate seconds until next occurrence of given UTC hour."""
    now_utc = datetime.now(timezone.utc)
    target = now_utc.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
    if now_utc >= target:
        target = target + timedelta(days=1)
    return int((target - now_utc).total_seconds())


def spawn_evaluation_worker() -> None:
    """Spawn a worker that computes evaluation metrics snapshot."""
    logger.info("Evaluation worker: launching evaluation task")
    try:
        task_id = f"evaluation_task_{uuid.uuid4().hex[:8]}"
        task_execution_manager.execute_task(
            task_id, lambda: run_evaluation_task(task_id)
        )
        logger.info(f"Evaluation worker: launched evaluation task {task_id}")
    except Exception as e:
        logger.error(f"Evaluation worker failed to launch task: {e}")
        raise


def run_evaluation_task(task_id: str) -> None:
    """Run the actual evaluation process (executed as a background task)."""
    logger.info(f"Evaluation task {task_id}: starting")
    try:
        worker = EvaluationWorker()
        worker.run()
        logger.info(f"Evaluation task {task_id}: completed successfully")
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Evaluation task {task_id} failed: {e}")


def spawn_discovery_worker() -> None:
    """Spawn a discovery worker that finds new laws from EUR-Lex asynchronously."""
    logger.info("Discovery worker: launching discovery task")

    try:
        # Generate unique task ID for this discovery run
        task_id = f"discovery_task_{uuid.uuid4().hex[:8]}"

        # Launch discovery as a separate background task
        task_execution_manager.execute_task(
            task_id, lambda: run_discovery_task(task_id)
        )

        logger.info(f"Discovery worker: launched discovery task {task_id}")

    except Exception as e:
        logger.error(f"Discovery worker failed to launch task: {e}")
        raise

    logger.info("Discovery worker: task launched successfully")


def run_discovery_task(task_id: str) -> None:
    """Run the actual discovery process (executed as a background task)."""
    logger.info(f"Discovery task {task_id}: starting")

    try:
        # Create and run discovery worker
        worker = DiscoveryWorker()
        worker.run()

        logger.info(f"Discovery task {task_id}: completed successfully")

    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Discovery task {task_id} failed: {e}")


def spawn_processing_worker() -> None:
    """Spawn a processing worker that processes discovered laws."""
    logger.info("Processing worker: launching summary task")

    try:
        # Generate unique task ID for this summary run
        task_id = f"summary_task_{uuid.uuid4().hex[:8]}"

        # Launch summary processing as a separate background task
        task_execution_manager.execute_task(task_id, lambda: run_summary_task(task_id))

        logger.info(f"Processing worker: launched summary task {task_id}")

    except Exception as e:
        logger.error(f"Processing worker failed to launch task: {e}")
        raise

    logger.info("Processing worker: task launched successfully")


def run_summary_task(task_id: str) -> None:
    """Run the actual summary processing (executed as a background task)."""
    logger.info(f"Summary task {task_id}: starting")

    try:
        # Create and run summary worker
        worker = SummaryWorker()
        worker.run()

        logger.info(f"Summary task {task_id}: completed successfully")

    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Summary task {task_id} failed: {e}")


def spawn_reconciliation_worker() -> None:
    """Spawn a reconciliation worker that checks for missing acts."""
    logger.info("Reconciliation worker: launching reconciliation task")

    try:
        # Generate unique task ID for this reconciliation run
        task_id = f"reconciliation_task_{uuid.uuid4().hex[:8]}"

        # Launch reconciliation as a separate background task
        task_execution_manager.execute_task(
            task_id, lambda: run_reconciliation_task(task_id)
        )

        logger.info(f"Reconciliation worker: launched reconciliation task {task_id}")

    except Exception as e:
        logger.error(f"Reconciliation worker failed to launch task: {e}")
        raise

    logger.info("Reconciliation worker: task launched successfully")


def run_reconciliation_task(task_id: str) -> None:
    """Run the actual reconciliation process (executed as a background task)."""
    logger.info(f"Reconciliation task {task_id}: starting")

    try:
        # Create and run reconciliation worker
        worker = ReconciliationWorker()
        worker.run()

        logger.info(f"Reconciliation task {task_id}: completed successfully")

    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Reconciliation task {task_id} failed: {e}")


def spawn_database_sync_worker() -> None:
    """Spawn a sync worker that synchronizes SQLite cache with PhariaData."""
    logger.info("Sync worker: launching database sync task")

    try:
        # Generate unique task ID for this sync run
        task_id = f"sync_task_{uuid.uuid4().hex[:8]}"

        # Launch sync as a separate background task
        task_execution_manager.execute_task(
            task_id, lambda: run_database_sync_task(task_id)
        )

        logger.info(f"Sync worker: launched sync task {task_id}")

    except Exception as e:
        logger.error(f"Sync worker failed to launch task: {e}")
        raise

    logger.info("Sync worker: task launched successfully")


def run_database_sync_task(task_id: str) -> None:
    """Run the actual sync process (executed as a background task)."""
    logger.info(f"Database Sync task {task_id}: starting")

    try:
        # Create and run sync worker
        worker = DatabaseSyncWorker()
        worker.run()

        logger.info(f"Sync task {task_id}: completed successfully")

    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"Sync task {task_id} failed: {e}")
        # Don't re-raise here as this runs in a background task


def start_background_dispatchers() -> None:
    """Start all background dispatcher loops using TaskExecutionManager."""

    logger.info("Starting background dispatchers")

    # Start discovery loop in background thread
    task_execution_manager.execute_task("discovery_loop", discovery_loop)

    # Start processing loop in background thread
    task_execution_manager.execute_task("processing_loop", processing_loop)

    # Start reconciliation loop in background thread
    task_execution_manager.execute_task("reconciliation_loop", reconciliation_loop)
    # Start sync loop in background thread
    settings = with_settings()
    if settings.storage_type == StorageBackendType.PHARIA_DATA_SYNCED_SQLITE.value:
        task_execution_manager.execute_task("database_sync_loop", database_sync_loop)

    task_execution_manager.execute_task(
        "evaluation_snapshot_loop", evaluation_snapshot_loop
    )

    logger.info("Background dispatchers started")
