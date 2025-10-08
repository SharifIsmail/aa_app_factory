from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import and_, func

from service.core.database.models import EvaluationMetrics, Law
from service.core.database.postgres_repository import PostgresRepository
from service.models import Category, LawStatus, OfficialJournalSeries


class ConfusionMatrix(BaseModel):
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class MetricScores(BaseModel):
    precision: float
    recall: float
    f1_score: float
    accuracy: float


class MetricUndefinedFlags(BaseModel):
    precision_undefined: bool
    recall_undefined: bool
    f1_undefined: bool
    accuracy_undefined: bool


class ConfidenceStats(BaseModel):
    average_confidence: float
    min_confidence: float
    max_confidence: float


class TeamRelevancyStats(BaseModel):
    most_relevant_teams: list[tuple[str, int]]


class RelevanceDistribution(BaseModel):
    ground_truth_relevant: int
    ground_truth_irrelevant: int
    predicted_relevant: int
    predicted_irrelevant: int


class ComputedEvaluationMetrics(BaseModel):
    total_samples: int
    successful_evaluations: int
    failed_evaluations: int
    confusion_matrix: ConfusionMatrix
    metrics: MetricScores
    undefined_flags: MetricUndefinedFlags
    confidence_stats: ConfidenceStats
    team_relevancy_stats: TeamRelevancyStats
    relevance_distribution: RelevanceDistribution


class EvaluationMetricsDAO:
    """Compute and persist evaluation metrics using Law as source of truth."""

    def __init__(self, repo: PostgresRepository) -> None:
        self.repo = repo

    def count_total_laws(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        journal_series: OfficialJournalSeries | None = None,
    ) -> int:
        """Count total laws in optional publication_date window (classified or not)."""
        with self.repo.session_scope() as session:
            query = session.query(Law)
            if start_date is not None:
                query = query.filter(Law.publication_date >= start_date)
            if end_date is not None:
                query = query.filter(Law.publication_date <= end_date)
            if journal_series is not None:
                query = query.filter(Law.oj_series_label == journal_series)
            return query.count()

    def get_earliest_publication_date(self) -> datetime | None:
        """Return the earliest publication_date in Law table, or None if empty."""
        with self.repo.session_scope() as session:
            return session.query(func.min(Law.publication_date)).scalar()

    def count_total_ai_classifications(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        journal_series: OfficialJournalSeries | None = None,
    ) -> tuple[int, int]:
        """Count total AI classifications"""
        with self.repo.session_scope() as session:
            query = session.query(Law).filter(Law.status == LawStatus.PROCESSED)
            if start_date is not None:
                query = query.filter(Law.publication_date >= start_date)
            if end_date is not None:
                query = query.filter(Law.publication_date <= end_date)
            if journal_series is not None:
                query = query.filter(Law.oj_series_label == journal_series)
            laws: list[Law] = query.all()

            likely_relevant = 0
            likely_not_relevant = 0

            for law in laws:
                teams = law.team_relevancy_classification or []

                if any(bool(t.get("is_relevant")) for t in teams):
                    likely_relevant += 1
                else:
                    likely_not_relevant += 1
            return likely_relevant, likely_not_relevant

    def compute_metrics_from_laws(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        journal_series: OfficialJournalSeries | None = None,
        *,
        raise_on_zero_accuracy: bool = True,
    ) -> ComputedEvaluationMetrics:
        """Compute confusion matrix and metrics from Law table."""
        with self.repo.session_scope() as session:
            query = session.query(Law).filter(
                and_(
                    Law.category != Category.OPEN,
                    Law.team_relevancy_classification.isnot(None),
                )
            )
            if start_date is not None:
                query = query.filter(Law.publication_date >= start_date)
            if end_date is not None:
                query = query.filter(Law.publication_date <= end_date)
            if journal_series is not None:
                query = query.filter(Law.oj_series_label == journal_series)
            laws: list[Law] = query.all()

        tp = fp = tn = fn = 0
        confidence_scores: list[float] = []
        team_relevance_counts: dict[str, int] = {}

        for law in laws:
            truth = law.category == Category.RELEVANT
            teams = law.team_relevancy_classification or []
            total = len(teams)
            relevant = sum(1 for t in teams if t.get("is_relevant"))
            pred = relevant > 0

            if truth and pred:
                tp += 1
            elif truth and not pred:
                fn += 1
            elif not truth and pred:
                fp += 1
            else:
                tn += 1

            if total:
                confidence_scores.append(relevant / total)

            for t in teams:
                if t.get("is_relevant"):
                    team_name = t.get("team_name", "")
                    if team_name:
                        team_relevance_counts[team_name] = (
                            team_relevance_counts.get(team_name, 0) + 1
                        )

        precision_denom = tp + fp
        precision_undefined = precision_denom == 0
        precision = 0.0 if precision_undefined else tp / precision_denom

        recall_denom = tp + fn
        recall_undefined = recall_denom == 0
        recall = 0.0 if recall_undefined else tp / recall_denom

        f1_undefined = (precision + recall) == 0.0
        f1 = 0.0 if f1_undefined else (2 * precision * recall) / (precision + recall)

        accuracy_denom = tp + tn + fp + fn
        accuracy_undefined = accuracy_denom == 0
        if accuracy_undefined and raise_on_zero_accuracy:
            raise ZeroDivisionError("Accuracy denominator is 0 (no samples).")
        accuracy = 0.0 if accuracy_undefined else (tp + tn) / accuracy_denom

        return ComputedEvaluationMetrics(
            total_samples=tp + tn + fp + fn,
            successful_evaluations=tp + tn + fp + fn,
            failed_evaluations=0,
            confusion_matrix=ConfusionMatrix(
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
            ),
            metrics=MetricScores(
                precision=precision,
                recall=recall,
                f1_score=f1,
                accuracy=accuracy,
            ),
            undefined_flags=MetricUndefinedFlags(
                precision_undefined=precision_undefined,
                recall_undefined=recall_undefined,
                f1_undefined=f1_undefined,
                accuracy_undefined=accuracy_undefined,
            ),
            confidence_stats=ConfidenceStats(
                average_confidence=(sum(confidence_scores) / len(confidence_scores))
                if confidence_scores
                else 0.0,
                min_confidence=min(confidence_scores) if confidence_scores else 0.0,
                max_confidence=max(confidence_scores) if confidence_scores else 0.0,
            ),
            team_relevancy_stats=TeamRelevancyStats(
                most_relevant_teams=sorted(
                    team_relevance_counts.items(), key=lambda x: x[1], reverse=True
                )[:5],
            ),
            relevance_distribution=RelevanceDistribution(
                ground_truth_relevant=tp + fn,
                ground_truth_irrelevant=tn + fp,
                predicted_relevant=tp + fp,
                predicted_irrelevant=tn + fn,
            ),
        )

    def save_snapshot(
        self,
        metrics: dict,
        *,
        window_start: datetime,
        window_end: datetime,
        filters: dict | None = None,
    ) -> None:
        with self.repo.session_scope() as session:
            cm = metrics.get("confusion_matrix", {})
            m = metrics.get("metrics", {})
            conf = metrics.get("confidence_stats", {})

            row = EvaluationMetrics(
                computed_at=datetime.now(timezone.utc),
                window_start=window_start,
                window_end=window_end,
                true_positives=int(cm.get("true_positives", 0)),
                false_positives=int(cm.get("false_positives", 0)),
                true_negatives=int(cm.get("true_negatives", 0)),
                false_negatives=int(cm.get("false_negatives", 0)),
                precision=float(m.get("precision", 0.0)),
                recall=float(m.get("recall", 0.0)),
                f1_score=float(m.get("f1_score", 0.0)),
                accuracy=float(m.get("accuracy", 0.0)),
                total_samples=int(metrics.get("total_samples", 0)),
                successful_evaluations=int(metrics.get("successful_evaluations", 0)),
                failed_evaluations=int(metrics.get("failed_evaluations", 0)),
                average_confidence=float(conf.get("average_confidence", 0.0))
                if conf
                else None,
                min_confidence=float(conf.get("min_confidence", 0.0)) if conf else None,
                max_confidence=float(conf.get("max_confidence", 0.0)) if conf else None,
                team_relevancy_stats=metrics.get("team_relevancy_stats"),
                relevance_distribution=metrics.get("relevance_distribution"),
                filters=filters,
            )
            session.add(row)

    def latest_snapshot(self) -> EvaluationMetrics | None:
        with self.repo.session_scope() as session:
            return (
                session.query(EvaluationMetrics)
                .order_by(EvaluationMetrics.id.desc())
                .first()
            )

    def get_snapshot_by_window(
        self, *, window_start: datetime, window_end: datetime
    ) -> EvaluationMetrics | None:
        with self.repo.session_scope() as session:
            return (
                session.query(EvaluationMetrics)
                .filter(
                    EvaluationMetrics.window_start == window_start,
                    EvaluationMetrics.window_end == window_end,
                )
                .order_by(EvaluationMetrics.computed_at.desc())
                .first()
            )

    def list_snapshots(
        self, offset: int = 0, limit: int = 100
    ) -> list[EvaluationMetrics]:
        with self.repo.session_scope() as session:
            return (
                session.query(EvaluationMetrics)
                .order_by(EvaluationMetrics.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
