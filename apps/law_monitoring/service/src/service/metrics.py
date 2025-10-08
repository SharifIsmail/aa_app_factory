from typing import Any

from loguru import logger
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from starlette.applications import Starlette

from service.core.database.laws_dao import LawsDAO
from service.core.database.postgres_repository import create_postgres_repository
from service.dependencies import with_settings

user_last_seen: Gauge = Gauge(
    "usecase_user_last_seen_timestamp_seconds",
    "Last‐seen UNIX timestamp (UTC) per user",
    ["user_id"],
)


user_endpoint_requests: Counter = Counter(
    "usecase_user_endpoint_requests_total",
    "Total HTTP requests per user and endpoint",
    ["user_id", "endpoint"],
)

# Reconciliation metrics
acts_reconciliation_missing: Gauge = Gauge(
    "acts_reconciliation_missing_current",
    "Current number of acts identified as missing during reconciliation",
)

# Background Worker Metrics
worker_runs_total: Counter = Counter(
    "law_monitoring_worker_runs_total",
    "Total number of worker runs by type and status",
    ["worker_type", "status"],
)

worker_run_duration_seconds: Histogram = Histogram(
    "law_monitoring_worker_run_duration_seconds",
    "Duration of worker runs in seconds",
    ["worker_type", "status"],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600],
)

worker_active_runs: Gauge = Gauge(
    "law_monitoring_worker_active_runs",
    "Number of currently active worker runs",
    ["worker_type"],
)

worker_last_run_timestamp: Gauge = Gauge(
    "law_monitoring_worker_last_run_timestamp_seconds",
    "Timestamp of last worker run",
    ["worker_type", "status"],
)

worker_executions_total: Counter = Counter(
    "law_monitoring_worker_executions_total",
    "Total worker execution attempts",
    ["worker_type", "work_started", "exit_reason"],
)

# Law Processing Metrics
laws_by_status: Gauge = Gauge(
    "law_monitoring_laws_by_status", "Number of laws by processing status", ["status"]
)

laws_processing_duration_seconds: Histogram = Histogram(
    "law_monitoring_laws_processing_duration_seconds",
    "Time spent processing individual laws",
    ["status"],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400],
)

laws_failure_count: Gauge = Gauge(
    "law_monitoring_laws_failure_count",
    "Number of laws by failure count",
    ["failure_count"],
)

discovery_laws_found: Counter = Counter(
    "law_monitoring_discovery_laws_found_total",
    "Total laws found during discovery runs",
)

discovery_laws_saved: Counter = Counter(
    "law_monitoring_discovery_laws_saved_total",
    "Total laws successfully saved during discovery",
)

discovery_laws_skipped: Counter = Counter(
    "law_monitoring_discovery_laws_skipped_total",
    "Total laws skipped (already exist) during discovery",
)

discovery_laws_failed: Counter = Counter(
    "law_monitoring_discovery_laws_failed_total",
    "Total laws failed to save during discovery",
)

summary_laws_processed: Counter = Counter(
    "law_monitoring_summary_laws_processed_total",
    "Total laws processed by summary worker",
    ["status"],
)

# Task-level timing metrics
law_processing_step_duration_seconds: Histogram = Histogram(
    "law_monitoring_step_duration_seconds",
    "Duration of individual processing steps",
    ["step_name", "status"],
    buckets=[1, 5, 10, 30, 60, 180, 300, 600],
)

# LLM call metrics
llm_call_duration_seconds: Histogram = Histogram(
    "law_monitoring_llm_call_duration_seconds",
    "Duration of LLM calls",
    ["purpose"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

# Web scraping metrics
web_scraping_duration_seconds: Histogram = Histogram(
    "law_monitoring_web_scraping_duration_seconds",
    "Duration of webpage fetching",
    ["success"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)


def update_laws_status_metrics() -> None:
    """Update gauges for current law status counts using database."""
    try:
        # Get database connection and DAO
        settings = with_settings()
        repo = create_postgres_repository(settings)
        dao = LawsDAO(repo)

        # Get status counts from database
        status_counts = dao.get_status_counts()
        failure_counts = dao.get_failure_counts()

        # Update status gauges
        laws_by_status.labels(status="raw").set(status_counts.get("RAW", 0))
        laws_by_status.labels(status="processing").set(
            status_counts.get("PROCESSING", 0)
        )
        laws_by_status.labels(status="processed").set(status_counts.get("PROCESSED", 0))
        laws_by_status.labels(status="failed").set(status_counts.get("FAILED", 0))

        # Clear and update failure count gauges
        laws_failure_count.clear()
        for failure_count, count in failure_counts.items():
            laws_failure_count.labels(failure_count=failure_count).set(count)

    except Exception as e:
        logger.error(f"Error updating law status metrics: {e}")


def with_metrics(app: Starlette) -> None:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics"],
    )
    instrumentator.instrument(app)
    instrumentator.add(metrics.default())

    # Add custom metrics updater - the lambda needs to accept one argument (info)
    def update_custom_metrics(info: Any) -> None:
        update_laws_status_metrics()

    instrumentator.add(lambda info: update_custom_metrics(info))

    instrumentator.expose(
        app, endpoint="/metrics", include_in_schema=False, should_gzip=True
    )
