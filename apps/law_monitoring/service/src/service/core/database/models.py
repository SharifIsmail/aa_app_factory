from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from service.models import Category, DocumentTypeLabel, LawStatus, OfficialJournalSeries

DATABASE_TABLE_PREFIX = "law_monitoring_"


class Base(DeclarativeBase):
    pass


class WorkerRun(Base):
    __abstract__ = True

    uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    errors: Mapped[List[str]] = mapped_column(JSON, default=list)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(uuid='{self.uuid}', status='{self.status}')>"
        )


class SummaryRun(WorkerRun):
    __tablename__ = DATABASE_TABLE_PREFIX + "summary_runs"

    processed: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    law_id: Mapped[Optional[str]] = mapped_column(String(100))
    processing_duration_seconds: Mapped[Optional[float]] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"<SummaryRun(uuid='{self.uuid}', status='{self.status}', processed={self.processed})>"


class DiscoveryRun(WorkerRun):
    __tablename__ = DATABASE_TABLE_PREFIX + "discovery_runs"

    total_laws_found: Mapped[Optional[int]] = mapped_column(Integer)
    successful_saves: Mapped[Optional[int]] = mapped_column(Integer)
    skipped_existing: Mapped[Optional[int]] = mapped_column(Integer)
    failed_saves: Mapped[Optional[int]] = mapped_column(Integer)
    discovered_laws: Mapped[List[str]] = mapped_column(JSON, default=list)

    def __repr__(self) -> str:
        return f"<DiscoveryRun(uuid='{self.uuid}', status='{self.status}', total_laws_found={self.total_laws_found})>"


class ReconciliationState(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "reconciliation_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    last_reconciliation_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    missing_acts_log: Mapped[List[dict]] = mapped_column(JSON, default=list)
    runs: Mapped[List["ReconciliationRun"]] = relationship(
        "ReconciliationRun", back_populates="state", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ReconciliationState(id={self.id}, last_reconciliation_date='{self.last_reconciliation_date}')>"


class ReconciliationRun(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "reconciliation_runs"
    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    state_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(DATABASE_TABLE_PREFIX + "reconciliation_state.id"),
        nullable=False,
    )
    query_start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    query_end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    eur_lex_acts_found: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_acts_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status_counts: Mapped[Dict[str, int]] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    state: Mapped["ReconciliationState"] = relationship(
        "ReconciliationState", back_populates="runs"
    )

    def __repr__(self) -> str:
        return f"<ReconciliationRun(run_id='{self.run_id}', eur_lex_acts_found={self.eur_lex_acts_found})>"


class ExecutionRecord(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "execution_records"
    execution_uuid: Mapped[str] = mapped_column(String(36), primary_key=True)
    worker_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False)
    invoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    work_started: Mapped[Optional[datetime]] = mapped_column(DateTime)
    exit_reason: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<ExecutionRecord(execution_uuid='{self.execution_uuid}', worker_type='{self.worker_type}', exit_reason='{self.exit_reason}')>"


class MissingLaw(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "missing_laws"
    file_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    expression_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    publication_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    detected_missing_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    folder: Mapped[Optional[str]] = mapped_column(String(255))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        return f"<MissingLaw(file_id='{self.file_id}', status='{self.status}', title='{self.title[:50]}...')>"


class DiscoveryState(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "discovery_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_successful_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    total_laws_discovered: Mapped[int] = mapped_column(Integer, default=0)
    total_discovery_runs: Mapped[int] = mapped_column(Integer, default=0)
    first_discovery_run: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Law(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "laws"

    # Primary identification
    law_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # Processing lifecycle
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[LawStatus] = mapped_column(
        SQLEnum(LawStatus), nullable=False, default=LawStatus.RAW
    )
    start_processing: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Source URLs and links
    expression_url: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)
    source_link: Mapped[Optional[str]] = mapped_column(Text)
    full_report_link: Mapped[Optional[str]] = mapped_column(Text)

    # Document dates
    publication_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    document_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    effect_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_validity_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notification_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Document content
    law_text_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    law_text: Mapped[Optional[str]] = mapped_column(Text)

    # Document classification and metadata
    document_type: Mapped[Optional[str]] = mapped_column(Text)
    document_type_label: Mapped[DocumentTypeLabel] = mapped_column(
        SQLEnum(DocumentTypeLabel), default=DocumentTypeLabel.UNKNOWN
    )
    oj_series_label: Mapped[OfficialJournalSeries] = mapped_column(
        SQLEnum(OfficialJournalSeries), default=OfficialJournalSeries.UNKNOWN
    )
    category: Mapped[Category] = mapped_column(SQLEnum(Category), default=Category.OPEN)
    eurovoc_labels: Mapped[Optional[List[str]]] = mapped_column(JSON)

    # Analysis results
    header_raw: Mapped[Optional[str]] = mapped_column(Text)
    subject_matter: Mapped[Optional[dict]] = mapped_column(JSON)
    timeline: Mapped[Optional[dict]] = mapped_column(JSON)
    roles_penalties: Mapped[Optional[dict]] = mapped_column(JSON)
    roles_raw: Mapped[Optional[str]] = mapped_column(Text)
    business_areas_affected: Mapped[Optional[str]] = mapped_column(Text)
    team_relevancy_classification: Mapped[List[Any]] = mapped_column(JSON, default=list)
    has_relevancy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Report generation
    html_report_path: Mapped[Optional[str]] = mapped_column(Text)
    report_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Error handling
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Law(law_id='{self.law_id}', status='{self.status}', title='{self.title[:50]}...')>"


class CompanyConfig(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "company_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_description: Mapped[Optional[str]] = mapped_column(Text)
    teams: Mapped[List["Team"]] = relationship(
        "Team", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CompanyConfig(id={self.id}, teams_count={len(self.teams)})>"


class Team(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "teams"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(DATABASE_TABLE_PREFIX + "company_config.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    daily_processes: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    relevant_laws_or_topics: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped["CompanyConfig"] = relationship(
        "CompanyConfig", back_populates="teams"
    )

    def __repr__(self) -> str:
        return (
            f"<Team(id={self.id}, name='{self.name}', department='{self.department}')>"
        )


class EvaluationMetrics(Base):
    __tablename__ = DATABASE_TABLE_PREFIX + "evaluation_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Confusion matrix
    true_positives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    false_positives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    true_negatives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    false_negatives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Aggregated metrics
    precision: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Totals
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_evaluations: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    failed_evaluations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Confidence statistics
    average_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    min_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    max_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Extra payloads as JSON for flexibility
    team_relevancy_stats: Mapped[Optional[dict]] = mapped_column(JSON)
    relevance_distribution: Mapped[Optional[dict]] = mapped_column(JSON)
    filters: Mapped[Optional[dict]] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<EvaluationMetrics(id={self.id}, computed_at='{self.computed_at.isoformat()}')>"
