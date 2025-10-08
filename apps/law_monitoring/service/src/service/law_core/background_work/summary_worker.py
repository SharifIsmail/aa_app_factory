import time

from loguru import logger

from service.core.database.laws_dao import LawsDAO
from service.core.database.models import Law
from service.core.database.postgres_repository import create_postgres_repository
from service.dependencies import with_settings
from service.law_core.background_work.base_worker import BaseWorker
from service.law_core.background_work.workers_constants import (
    MAX_LAW_RETRY_ATTEMPTS,
    SUMMARY_PROCESSING_TIMEOUT_HOURS,
)
from service.law_core.law_report_service import LawReportService
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.law_core.summary.summary_work_log_manager import create_work_log
from service.law_core.tools.visit_webpage_tool import VisitWebpageUserAgentTool
from service.metrics import laws_processing_duration_seconds, summary_laws_processed
from service.models import LawStatus


class SummaryWorker(BaseWorker):
    """Worker for processing and summarizing discovered legal acts."""

    def __init__(self) -> None:
        """Initialize the summary worker."""
        settings = with_settings()
        self.postgres_repo = create_postgres_repository(settings)
        self.laws_dao = LawsDAO(self.postgres_repo)

        self.storage_backend = get_configured_storage_backend()
        super().__init__("summary")

    def _do_work(self) -> dict:
        """
        Perform the summary work.

        1. Look for stuck PROCESSING laws (>1 hour old)
        2. If found, retry those
        3. Otherwise, pick first RAW law
        4. Update status to PROCESSING with timestamp
        5. Process the law
        6. Update status to PROCESSED

        Returns:
            Dictionary with processing results
        """
        # Check for stuck processing laws first
        stuck_laws = self.laws_dao.get_stuck_processing_laws(
            timeout_hours=SUMMARY_PROCESSING_TIMEOUT_HOURS
        )

        law: Law | None = None

        if stuck_laws:
            # Process the first stuck law
            law = stuck_laws[0]
            logger.info(f"Summary worker: Found stuck law {law.law_id}, retrying")
        else:
            # Get the oldest RAW law
            law = self.laws_dao.get_oldest_raw_law()
            if not law:
                logger.info("Summary worker: No RAW laws to process")
                return {"processed": 0, "reason": "no_pending_laws"}

        law_file_id = str(law.law_id)

        # Start timing the entire law processing
        law_processing_start = time.time()

        self.laws_dao.mark_processing(law_file_id)

        try:
            expression_url = str(law.expression_url)
            pdf_url = str(law.pdf_url)

            if not expression_url:
                raise ValueError(
                    f"No expression_url found in law data for {law_file_id}"
                )

            if not pdf_url:
                raise ValueError(f"No pdf_url found in law data for {law_file_id}")

            logger.info(
                f"Summary worker: Fetching law text from {expression_url} for law {law_file_id}"
            )

            webpage_tool = VisitWebpageUserAgentTool(
                data_storage=None,
                execution_id=law_file_id,
                work_log=None,
                repo_key=f"law_content_{law_file_id}",
            )

            law_text = webpage_tool.forward(expression_url)

            if not law_text or law_text.startswith("Error:"):
                raise ValueError(f"Failed to fetch law text: {law_text}")

            logger.info(
                f"Summary worker: Successfully fetched law text ({len(law_text)} characters) for law {law_file_id}"
            )

            work_log = create_work_log(law_file_id)

            logger.info(
                f"Summary worker: Starting summary computation for law {law_file_id}"
            )

            # Extract metadata from law for enhanced report generation
            metadata = {
                "title": law.title,
                "publication_date": law.publication_date.isoformat()  # type: ignore
                if law.publication_date
                else None,
                "document_date": law.document_date.isoformat()  # type: ignore
                if law.document_date
                else None,
                "effect_date": law.effect_date.isoformat() if law.effect_date else None,  # type: ignore
                "end_validity_date": law.end_validity_date.isoformat()  # type: ignore
                if law.end_validity_date
                else None,
                "notification_date": law.notification_date.isoformat()  # type: ignore
                if law.notification_date
                else None,
                "eurovoc_labels": law.eurovoc_labels or [],
                "document_type_label": law.document_type_label.value  # type: ignore
                if law.document_type_label
                else "N/A",
                "oj_series_label": law.oj_series_label.value  # type: ignore
                if law.oj_series_label
                else "N/A",
            }

            try:
                law_report_service = LawReportService(
                    act_id=law_file_id, work_log=work_log
                )
                html_report_path = law_report_service.analyze_law_and_generate_report(
                    expression_url=expression_url,
                    pdf_url=pdf_url,
                    law_text=law_text,
                    metadata=metadata,
                )
            except Exception as summary_error:
                logger.error(
                    f"Summary worker: Exception during law analysis and report generation for law {law_file_id}: {summary_error}"
                )
                raise ValueError(
                    f"Law analysis and report generation failed with exception for law {law_file_id}: {summary_error}"
                ) from summary_error

            if html_report_path:
                # Mark as processed with report path and law text
                self.laws_dao.mark_processed(law_file_id, html_report_path, law_text)
                logger.info(
                    f"Summary worker: law analysis and report generation completed for law {law_file_id}, report saved to {html_report_path}"
                )
            else:
                logger.error(
                    f"Summary worker: law analysis and report generation returned empty/None result for law {law_file_id}"
                )
                raise ValueError(
                    f"Law analysis and report generation failed - no report generated for law {law_file_id}"
                )

            # Calculate total processing time and update metrics
            total_duration = time.time() - law_processing_start
            laws_processing_duration_seconds.labels(status="success").observe(
                total_duration
            )
            summary_laws_processed.labels(status="success").inc()

            logger.info(
                f"Summary worker: Successfully processed law {law_file_id} in {total_duration:.2f} seconds"
            )
            return {
                "processed": 1,
                "law_id": law_file_id,
                "status": "success",
                "processing_duration_seconds": total_duration,
            }

        except Exception as e:
            # Calculate duration for failed processing
            total_duration = time.time() - law_processing_start
            laws_processing_duration_seconds.labels(status="failed").observe(
                total_duration
            )
            return self._handle_processing_failure(law_file_id, e)

    def _handle_processing_failure(
        self, law_file_id: str, exception: Exception
    ) -> dict:
        """
        Handle processing failure for a law.

        Tracks failure count, decides whether to retry or move to failed folder,
        and returns appropriate response.
        """
        error_msg = f"Failed to process law {law_file_id}: {str(exception)}"
        logger.error(f"Summary worker: {error_msg}")

        # Get current law to check failure count
        law = self.laws_dao.get(law_file_id)
        if not law:
            logger.error(
                f"Summary worker: Could not find law {law_file_id} in database"
            )
            return {"processed": 0, "reason": "law_not_found", "error": error_msg}

        current_failure_count = law.failure_count or 0
        new_failure_count = current_failure_count + 1

        if new_failure_count >= MAX_LAW_RETRY_ATTEMPTS:
            # Mark as failed
            self.laws_dao.mark_failed(law_file_id, error_msg)
            summary_laws_processed.labels(status="failed").inc()

            logger.error(
                f"Summary worker: Law {law_file_id} failed {new_failure_count} times, marking as FAILED"
            )
            return {
                "processed": 0,
                "law_id": law_file_id,
                "status": "failed_permanently",
                "failure_count": new_failure_count,
                "error": error_msg,
            }
        else:
            # Mark as failed but keep for retry
            self.laws_dao.mark_failed(law_file_id, error_msg)
            # Reset status to RAW for retry
            with self.laws_dao.repo.session_scope() as session:
                law = session.get(Law, law_file_id)
                if law:
                    law.status = LawStatus.RAW

            summary_laws_processed.labels(status="retry").inc()

            logger.warning(
                f"Summary worker: Law {law_file_id} failed {new_failure_count} times, will retry later"
            )
            return {
                "processed": 0,
                "law_id": law_file_id,
                "status": "failed_retry",
                "failure_count": new_failure_count,
                "error": error_msg,
            }
