"""
Reconciliation worker that ensures no legal acts are missed.

This worker periodically checks EUR-Lex for acts and verifies we have
processed them, logging any missing acts for monitoring.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from service.core.database.laws_dao import LawsDAO
from service.core.database.postgres_repository import create_postgres_repository
from service.core.utils.utils import generate_url_hash
from service.dependencies import with_settings
from service.law_core.background_work.base_worker import BaseWorker
from service.law_core.background_work.workers_constants import (
    DATA_FOLDER,
    EUROVOC_BACKFILL_LOOKBACK_DAYS,
    EUROVOC_BACKFILL_MAX_LAWS,
    EUROVOC_BACKFILL_MODE,
    MISSING_ACTS_LOG_FILE,
    RAW_ACT_MAX_AGE_HOURS,
    RECONCILIATION_DATA_FILE,
    RECONCILIATION_FIRST_RUN_LOOKBACK_HOURS,
    RECONCILIATION_MAX_TIME_WINDOW_DAYS,
    RECONCILIATION_SAFETY_MARGIN_HOURS,
    REPORTS_FOLDER,
)
from service.law_core.eur_lex_service import eur_lex_service
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.metrics import acts_reconciliation_missing
from service.models import LawStatus


class ReconciliationWorker(BaseWorker):
    """Worker that reconciles discovered acts with processed ones."""

    def __init__(self) -> None:
        """Initialize the reconciliation worker."""
        super().__init__("reconciliation")

        # Initialize database components
        settings = with_settings()
        self.postgres_repo = create_postgres_repository(settings)
        self.laws_dao = LawsDAO(self.postgres_repo)

        # Keep storage backend for reconciliation data and reports
        self.storage_backend = get_configured_storage_backend()

    @property
    def worker_name(self) -> str:
        """Return the unique name of this worker."""
        return "reconciliation_worker"

    def _load_reconciliation_data(self) -> Dict[str, Any]:
        """Load reconciliation state data from storage."""
        if self.storage_backend.file_exists(DATA_FOLDER, RECONCILIATION_DATA_FILE):
            data_str = self.storage_backend.load_file(
                DATA_FOLDER, RECONCILIATION_DATA_FILE
            )
            if data_str:
                return json.loads(data_str)

        # Return default structure if file doesn't exist
        return {
            "last_reconciliation_date": None,
            "reconciliation_runs": [],
            "missing_acts_log": [],
        }

    def _save_reconciliation_data(self, data: Dict[str, Any]) -> None:
        """Save reconciliation state data to storage."""
        data_str = json.dumps(data, indent=2, default=str)
        self.storage_backend.save_file(DATA_FOLDER, RECONCILIATION_DATA_FILE, data_str)
        logger.info(
            f"Saved reconciliation data to {DATA_FOLDER}/{RECONCILIATION_DATA_FILE}"
        )

    def _calculate_time_window(
        self, last_reconciliation_date: Optional[str]
    ) -> Tuple[datetime, datetime]:
        """
        Calculate the time window for reconciliation.

        Args:
            last_reconciliation_date: ISO format string of last reconciliation date

        Returns:
            Tuple of (start_date, end_date) for reconciliation window
        """
        end_date = datetime.now(timezone.utc)

        if last_reconciliation_date:
            try:
                # Parse the last reconciliation date - use exact same pattern as discovery worker
                last_run = datetime.fromisoformat(last_reconciliation_date)
                # Ensure last_run is timezone-aware in UTC
                if (
                    last_run.tzinfo is not None
                    and last_run.tzinfo.utcoffset(last_run) is not None
                ):
                    last_run = last_run.astimezone(timezone.utc)
                else:
                    last_run = last_run.replace(tzinfo=timezone.utc)
                # Apply safety margin by going back RECONCILIATION_SAFETY_MARGIN_HOURS
                start_date = last_run - timedelta(
                    hours=RECONCILIATION_SAFETY_MARGIN_HOURS
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid last_reconciliation_date '{last_reconciliation_date}': {e}"
                )
                # Fall back to configured default
                start_date = end_date - timedelta(
                    hours=RECONCILIATION_FIRST_RUN_LOOKBACK_HOURS
                )
        else:
            # First run - go back configured number of hours
            start_date = end_date - timedelta(
                hours=RECONCILIATION_FIRST_RUN_LOOKBACK_HOURS
            )
            logger.info(
                f"First reconciliation run - checking last {RECONCILIATION_FIRST_RUN_LOOKBACK_HOURS} hours"
            )

        # Validate time window sanity
        if start_date >= end_date:
            logger.warning(
                f"Invalid time window: start_date ({start_date}) >= end_date ({end_date})"
            )
            # Fix by using last 24 hours
            start_date = end_date - timedelta(hours=24)

        # Limit maximum time window to prevent overwhelming EUR-Lex
        if (end_date - start_date).days > RECONCILIATION_MAX_TIME_WINDOW_DAYS:
            logger.warning(
                f"Time window too large ({(end_date - start_date).days} days), limiting to {RECONCILIATION_MAX_TIME_WINDOW_DAYS} days"
            )
            start_date = end_date - timedelta(days=RECONCILIATION_MAX_TIME_WINDOW_DAYS)

        logger.info(
            f"Reconciliation time window: {start_date.isoformat()} to {end_date.isoformat()}"
        )
        return start_date, end_date

    def _check_act_status(self, expression_url: str) -> Tuple[str, str, Optional[str]]:
        """
        Check act status using database.

        Args:
            expression_url: EUR-Lex expression URL

        Returns:
            (status, location, error_reason) where:
            - status: "ok", "failed", "error"
            - location: "processed", "raw", "failed", or "missing"
            - error_reason: Description of issue (None if status="ok")
        """
        file_id = generate_url_hash(expression_url)

        # Check if law exists in database
        law = self.laws_dao.get(file_id)

        if not law:
            return "error", "missing", "Law not found in database"

        # Check status
        if law.status == LawStatus.PROCESSED:
            # Validate processed law has required data
            if not law.html_report_path:
                return "error", "processed", "Processed law missing report path"

            # Check if report file exists
            report_filename = f"act_{file_id.replace('law_', '')}.html"
            if not self.storage_backend.file_exists(REPORTS_FOLDER, report_filename):
                return "error", "processed", "Report file not found"

            return "ok", "processed", None

        elif law.status == LawStatus.FAILED:
            return "error", "failed", "Law marked as failed"

        elif law.status == LawStatus.RAW:
            # Check if law has been stuck in RAW status too long
            if law.discovered_at:
                age_hours = (datetime.now() - law.discovered_at).total_seconds() / 3600
                if age_hours > RAW_ACT_MAX_AGE_HOURS:
                    return (
                        "error",
                        "raw",
                        f"Law stuck in RAW status for {age_hours:.1f} hours",
                    )

            return "ok", "raw", None

        elif law.status == LawStatus.PROCESSING:
            # Check if processing has been stuck
            if law.start_processing:
                age_hours = (
                    datetime.now() - law.start_processing
                ).total_seconds() / 3600
                if age_hours > 2:  # 2 hours timeout for processing
                    return (
                        "error",
                        "processing",
                        f"Law stuck in PROCESSING status for {age_hours:.1f} hours",
                    )

            return "ok", "processing", None

        else:
            return "error", "unknown", f"Unknown law status: {law.status}"

    def _save_missing_acts_log(self, missing_acts: List[Dict[str, Any]]) -> None:
        """Save missing acts log to storage."""
        if not missing_acts:
            return

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "missing_acts_count": len(missing_acts),
            "missing_acts": missing_acts,
        }

        log_str = json.dumps(log_data, indent=2, default=str)
        self.storage_backend.save_file(DATA_FOLDER, MISSING_ACTS_LOG_FILE, log_str)
        logger.info(
            f"Saved missing acts log with {len(missing_acts)} missing acts to {DATA_FOLDER}/{MISSING_ACTS_LOG_FILE}"
        )

    def _do_work(self) -> Dict[str, Any]:
        """
        Perform reconciliation work.

        Returns:
            Dictionary with reconciliation results
        """
        logger.info("Starting reconciliation worker")

        # Load reconciliation data
        reconciliation_data = self._load_reconciliation_data()
        last_reconciliation_date = reconciliation_data.get("last_reconciliation_date")

        # Calculate time window
        start_date, end_date = self._calculate_time_window(last_reconciliation_date)

        # Query EUR-Lex for acts in the time window
        try:
            logger.info(f"Querying EUR-Lex for acts from {start_date} to {end_date}")
            legal_acts_response = eur_lex_service.get_legal_acts_by_date_range(
                start_date, end_date
            )
            eur_lex_acts = legal_acts_response.legal_acts
            logger.info(f"Found {len(eur_lex_acts)} acts in EUR-Lex")
        except Exception as e:
            logger.error(f"Failed to query EUR-Lex: {e}")
            return {
                "status": "error",
                "error": f"EUR-Lex query failed: {str(e)}",
                "eur_lex_acts_found": 0,
                "missing_acts_count": 0,
            }

        # Check each act
        missing_acts = []
        status_counts = {"ok": 0, "failed": 0, "error": 0}

        for act in eur_lex_acts:
            try:
                status, location, error_reason = self._check_act_status(
                    act.expression_url
                )
                status_counts[status] += 1

                if status != "ok":
                    missing_act = {
                        "expression_url": act.expression_url,
                        "title": act.title,
                        "publication_date": act.publication_date.isoformat(),
                        "status": status,
                        "location": location,
                        "error_reason": error_reason,
                        "detected_at": datetime.now().isoformat(),
                    }
                    missing_acts.append(missing_act)
                    logger.warning(
                        f"Missing/problematic act: {act.title} ({act.expression_url}) - {status}: {error_reason}"
                    )

            except Exception as e:
                logger.error(f"Error checking act {act.expression_url}: {e}")
                status_counts["error"] += 1
                missing_acts.append(
                    {
                        "expression_url": act.expression_url,
                        "title": act.title,
                        "publication_date": act.publication_date.isoformat(),
                        "status": "error",
                        "location": "unknown",
                        "error_reason": f"Exception during check: {str(e)}",
                        "detected_at": datetime.now().isoformat(),
                    }
                )

        # Save missing acts log
        self._save_missing_acts_log(missing_acts)

        # Update reconciliation data
        run_data = {
            "run_id": f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "query_start_date": start_date.isoformat(),
            "query_end_date": end_date.isoformat(),
            "eur_lex_acts_found": len(eur_lex_acts),
            "missing_acts_count": len(missing_acts),
            "status_counts": status_counts,
            "timestamp": datetime.now().isoformat(),
        }

        reconciliation_data["last_reconciliation_date"] = datetime.now().isoformat()
        reconciliation_data["reconciliation_runs"].append(run_data)
        reconciliation_data["missing_acts_log"] = missing_acts

        # Keep only last 10 runs to prevent data growth
        if len(reconciliation_data["reconciliation_runs"]) > 10:
            reconciliation_data["reconciliation_runs"] = reconciliation_data[
                "reconciliation_runs"
            ][-10:]

        self._save_reconciliation_data(reconciliation_data)

        # Update metrics
        acts_reconciliation_missing.set(len(missing_acts))

        logger.info(
            f"Reconciliation completed: {len(eur_lex_acts)} acts checked, "
            f"{len(missing_acts)} missing/problematic acts found"
        )

        result = {
            "status": "completed",
            "eur_lex_acts_found": len(eur_lex_acts),
            "missing_acts_count": len(missing_acts),
            "status_counts": status_counts,
            "query_start_date": start_date.isoformat(),
            "query_end_date": end_date.isoformat(),
            # Pre-fill error key for downstream consumers, will be overwritten on success
            "eurovoc_backfill_error": None,
        }

        # --- EuroVoc backfill pass ---
        # Iterate over laws based on configured backfill mode and refresh
        # missing metadata (EuroVoc labels and other optional fields).
        try:
            if EUROVOC_BACKFILL_MODE == "all":
                logger.info(
                    "EuroVoc backfill: scanning ALL laws (capped) for missing labels"
                )
                laws_to_check = self.laws_dao.list_by_date_range(
                    start_date=None, end_date=None, limit=EUROVOC_BACKFILL_MAX_LAWS
                )
            else:
                backfill_end = datetime.now()
                backfill_start = backfill_end - timedelta(
                    days=EUROVOC_BACKFILL_LOOKBACK_DAYS
                )

                logger.info(
                    f"EuroVoc backfill: scanning laws from {backfill_start.date()} to {backfill_end.date()} for missing labels"
                )

                laws_to_check = self.laws_dao.list_by_date_range(
                    start_date=backfill_start,
                    end_date=backfill_end,
                    limit=EUROVOC_BACKFILL_MAX_LAWS,
                )

            updated_count = 0
            checked_count = 0
            for law in laws_to_check:
                checked_count += 1
                labels = law.eurovoc_labels
                labels_missing = labels is None or (
                    isinstance(labels, list) and len(labels) == 0
                )
                if not labels_missing:
                    continue

                # Re-fetch this specific act directly by stored expression_url.
                try:
                    refreshed = eur_lex_service.get_legal_act_by_expression_url(
                        law.expression_url
                    )
                    if refreshed:
                        update_fields: dict[str, Any] = {}

                        def set_if_missing(
                            field_name: str, current_value: Any, refreshed_value: Any
                        ) -> None:
                            if not current_value and refreshed_value:
                                update_fields[field_name] = refreshed_value

                        # EuroVoc labels
                        if labels_missing and refreshed.eurovoc_labels:
                            update_fields["eurovoc_labels"] = refreshed.eurovoc_labels

                        # Also repair other optional metadata if missing
                        set_if_missing("pdf_url", law.pdf_url, refreshed.pdf_url)
                        set_if_missing(
                            "document_type_label",
                            law.document_type_label,
                            refreshed.document_type_label,
                        )
                        set_if_missing(
                            "document_type", law.document_type, refreshed.document_type
                        )
                        set_if_missing(
                            "oj_series_label",
                            law.oj_series_label,
                            refreshed.oj_series_label,
                        )
                        set_if_missing(
                            "document_date", law.document_date, refreshed.document_date
                        )
                        set_if_missing(
                            "effect_date", law.effect_date, refreshed.effect_date
                        )
                        set_if_missing(
                            "end_validity_date",
                            law.end_validity_date,
                            refreshed.end_validity_date,
                        )
                        set_if_missing(
                            "notification_date",
                            law.notification_date,
                            refreshed.notification_date,
                        )

                        if update_fields:
                            self.laws_dao.update_law_fields(
                                law_id=law.law_id,
                                update_fields=update_fields,
                            )
                            updated_count += 1
                except Exception as e:
                    logger.warning(
                        f"EuroVoc backfill: failed refresh for law_id={law.law_id}: {e}"
                    )

            logger.info(
                f"EuroVoc backfill complete: checked={checked_count}, updated={updated_count} laws"
            )
            result["eurovoc_backfill_checked"] = checked_count
            result["eurovoc_backfill_updated"] = updated_count
        except Exception as e:
            logger.error(f"EuroVoc backfill failed: {e}")
            result["eurovoc_backfill_error"] = str(e)

        return result
