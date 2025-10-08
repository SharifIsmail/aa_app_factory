from datetime import date, datetime, timedelta, timezone

from loguru import logger

from service.core.database.evaluation_metrics_dao import EvaluationMetricsDAO
from service.core.database.postgres_repository import create_postgres_repository
from service.dependencies import with_settings
from service.law_core.background_work.base_worker import BaseWorker


class EvaluationWorker(BaseWorker):
    """Worker to compute and persist evaluation metrics snapshots."""

    def __init__(self) -> None:
        settings = with_settings()
        self.postgres_repo = create_postgres_repository(settings)
        self.metrics_dao = EvaluationMetricsDAO(self.postgres_repo)
        super().__init__("evaluation")

    def _do_work(self) -> dict:
        """Compute and persist rolling 1d/7d/30d and cumulative-to-yesterday snapshots."""
        now = datetime.now(timezone.utc)
        anchor = (now - timedelta(days=1)).date()  # yesterday (UTC)

        def start_of(d: date) -> datetime:
            return datetime(d.year, d.month, d.day, 0, 0, 0, 0, tzinfo=timezone.utc)

        def end_of(d: date) -> datetime:
            return datetime(
                d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=timezone.utc
            )

        # Windows
        day_start, day_end = start_of(anchor), end_of(anchor)
        week_start = start_of(anchor - timedelta(days=6))
        week_end = day_end
        month_start = start_of(anchor - timedelta(days=29))
        month_end = day_end

        # Earliest for cumulative
        earliest = self.metrics_dao.get_earliest_publication_date()
        if earliest is not None and earliest.tzinfo is None:
            earliest = earliest.replace(tzinfo=timezone.utc)
        cum_start = earliest
        cum_end = day_end

        results: list[dict] = []

        def compute_and_save(
            window_start: datetime | None, window_end: datetime, window_type: str
        ) -> dict:
            if window_start is not None:
                existing = self.metrics_dao.get_snapshot_by_window(
                    window_start=window_start, window_end=window_end
                )
                if existing:
                    logger.info(
                        f"Evaluation worker: snapshot exists for {window_type}, skipping"
                    )
                    return {"status": "skipped_existing", "window_type": window_type}

            computed = self.metrics_dao.compute_metrics_from_laws(
                start_date=window_start, end_date=window_end
            )
            self.metrics_dao.save_snapshot(
                computed.model_dump(),
                window_start=window_start or day_start,
                window_end=window_end,
                filters={"window_type": window_type, "anchor_date": anchor.isoformat()},
            )
            return {
                "status": "saved",
                "window_type": window_type,
                "samples": computed.total_samples,
            }

        results.append(compute_and_save(day_start, day_end, "rolling_1d"))
        results.append(compute_and_save(week_start, week_end, "rolling_7d"))
        results.append(compute_and_save(month_start, month_end, "rolling_30d"))
        if cum_start is not None:
            results.append(
                compute_and_save(cum_start, cum_end, "cumulative_to_yesterday")
            )

        return {"anchor": anchor.isoformat(), "results": results}
