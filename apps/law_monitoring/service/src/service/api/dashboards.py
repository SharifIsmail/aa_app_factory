from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from service.core.database.evaluation_metrics_dao import EvaluationMetricsDAO
from service.core.database.laws_dao import LawsDAO
from service.core.database.postgres_repository import create_postgres_repository
from service.core.dependencies.authorization import access_permission
from service.dependencies import with_settings
from service.models import OfficialJournalSeries

dashboards_router = APIRouter(
    prefix="/dashboard", dependencies=[Depends(access_permission)]
)


class AIClassificationCounts(BaseModel):
    likely_relevant: int
    likely_not_relevant: int


class HumanDecisionCounts(BaseModel):
    relevant: int
    not_relevant: int
    awaiting_decision: int | None = None


class ClassificationOverviewMetrics(BaseModel):
    recall: float


class ClassificationOverviewResponse(BaseModel):
    total_acts: int
    total_evaluations: int
    ai_classification: AIClassificationCounts
    human_decision: HumanDecisionCounts
    metrics: ClassificationOverviewMetrics


class LegalActTimeline(BaseModel):
    date: datetime
    human_decision: HumanDecisionCounts
    legal_acts: int


class LegalActTimelineResponse(BaseModel):
    total_legal_acts: int
    legal_acts: list[LegalActTimeline]


class DepartmentRelevanceCount(BaseModel):
    department: str
    relevant_acts: int


class DepartmentsOverviewResponse(BaseModel):
    total_relevant_acts: int
    departments: list[DepartmentRelevanceCount]


class EurovocDescriptorCount(BaseModel):
    descriptor: str
    frequency: int


class EurovocOverviewResponse(BaseModel):
    total_descriptors: int
    descriptors: list[EurovocDescriptorCount]


@dashboards_router.get(
    "/classification-overview", response_model=ClassificationOverviewResponse
)
def classification_overview(
    start_date: date | None = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: date | None = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
    journal_series: OfficialJournalSeries | None = Query(
        None, description="Filter by official journal series (optional)"
    ),
) -> ClassificationOverviewResponse:
    settings = with_settings()
    repo = create_postgres_repository(settings)

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())

    metrics_dao = EvaluationMetricsDAO(repo)
    computed = metrics_dao.compute_metrics_from_laws(
        start_date=start_datetime,
        end_date=end_datetime,
        journal_series=journal_series,
        raise_on_zero_accuracy=False,
    )
    total_laws = metrics_dao.count_total_laws(
        start_date=start_datetime, end_date=end_datetime, journal_series=journal_series
    )
    likely_relevant, likely_not_relevant = metrics_dao.count_total_ai_classifications(
        start_date=start_datetime, end_date=end_datetime, journal_series=journal_series
    )
    human_decision_relevant = computed.relevance_distribution.ground_truth_relevant
    human_decision_not_relevant = (
        computed.relevance_distribution.ground_truth_irrelevant
    )
    awaiting_decision = (
        total_laws - human_decision_relevant - human_decision_not_relevant
    )

    return ClassificationOverviewResponse(
        total_acts=total_laws,
        total_evaluations=computed.total_samples,
        ai_classification=AIClassificationCounts(
            likely_relevant=likely_relevant,
            likely_not_relevant=likely_not_relevant,
        ),
        human_decision=HumanDecisionCounts(
            relevant=human_decision_relevant,
            not_relevant=human_decision_not_relevant,
            awaiting_decision=awaiting_decision,
        ),
        metrics=ClassificationOverviewMetrics(recall=computed.metrics.recall),
    )


@dashboards_router.get("/legal-act-timeline", response_model=LegalActTimelineResponse)
def legal_act_timeline(
    start_date: date | None = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: date | None = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
    journal_series: OfficialJournalSeries | None = Query(
        None, description="Filter by official journal series (optional)"
    ),
) -> LegalActTimelineResponse:
    settings = with_settings()
    repo = create_postgres_repository(settings)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())

    laws_dao = LawsDAO(repo)

    # Get legal acts timeline data with optional journal series filter
    rows = laws_dao.get_daily_human_decision_timeline(
        start_date=start_datetime, end_date=end_datetime, journal_series=journal_series
    )

    total_acts = sum(row["legal_acts"] for row in rows)

    items: list[LegalActTimeline] = [
        LegalActTimeline(
            date=row["date"],
            human_decision=HumanDecisionCounts(
                relevant=row["relevant"],
                not_relevant=row["not_relevant"],
                awaiting_decision=row["awaiting_decision"],
            ),
            legal_acts=row["legal_acts"],
        )
        for row in rows
    ]

    return LegalActTimelineResponse(total_legal_acts=total_acts, legal_acts=items)


@dashboards_router.get(
    "/departments-overview", response_model=DepartmentsOverviewResponse
)
def departments_overview(
    start_date: date | None = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: date | None = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
    journal_series: OfficialJournalSeries | None = Query(
        None, description="Filter by official journal series (optional)"
    ),
) -> DepartmentsOverviewResponse:
    """
    Get count of relevant legal acts per department within a date range.

    Returns departments ordered by number of relevant legal acts (descending).
    Only includes departments that have at least one relevant legal act.
    """
    settings = with_settings()
    repo = create_postgres_repository(settings)

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())

    laws_dao = LawsDAO(repo)

    # Get department relevance counts and total in one query
    department_data, total_relevant_acts = laws_dao.get_department_relevance_counts(
        start_date=start_datetime, end_date=end_datetime, journal_series=journal_series
    )

    # Convert to response format
    departments = [
        DepartmentRelevanceCount(
            department=item.department,
            relevant_acts=item.relevant_acts,
        )
        for item in department_data
    ]

    return DepartmentsOverviewResponse(
        total_relevant_acts=total_relevant_acts, departments=departments
    )


@dashboards_router.get("/eurovoc-overview", response_model=EurovocOverviewResponse)
def eurovoc_overview(
    start_date: date | None = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: date | None = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
    journal_series: OfficialJournalSeries | None = Query(
        None, description="Filter by official journal series (optional)"
    ),
) -> EurovocOverviewResponse:
    """
    Get frequency count of EuroVoc descriptors within a date range.

    Returns EuroVoc descriptors ordered by frequency (descending).
    Only includes processed legal acts that have EuroVoc descriptors.
    """
    settings = with_settings()
    repo = create_postgres_repository(settings)

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())

    laws_dao = LawsDAO(repo)

    # Get EuroVoc descriptor frequency counts
    descriptor_data = laws_dao.get_eurovoc_descriptor_counts(
        start_date=start_datetime, end_date=end_datetime, journal_series=journal_series
    )

    # Convert to response format
    descriptors = [
        EurovocDescriptorCount(descriptor=item.descriptor, frequency=item.frequency)
        for item in descriptor_data
    ]

    return EurovocOverviewResponse(
        total_descriptors=len(descriptors), descriptors=descriptors
    )
