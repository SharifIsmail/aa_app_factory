"""Temporary Adapters for converting between Pydantic models and ORM models."""

from datetime import datetime
from typing import List, Optional

from service.core.database.models import Law
from service.models import (
    Category,
    DocumentTypeLabel,
    LawData,
    LawStatus,
    LegalAct,
    OfficialJournalSeries,
    TeamRelevancy,
    TeamRelevancyWithCitations,
)


def law_to_lawdata(law: Law) -> LawData:
    """Convert ORM Law to Pydantic LawData."""
    return LawData(
        title=law.title,
        expression_url=law.expression_url,
        pdf_url=law.pdf_url or "",
        publication_date=law.publication_date,
        discovered_at=law.discovered_at,
        law_file_id=law.law_id,
        law_text=law.law_text,
        status=law.status,
        subject_matter_text=_extract_subject_matter_from_json(law.subject_matter),
        category=law.category,
        eurovoc_labels=law.eurovoc_labels,
        document_date=law.document_date,
        effect_date=law.effect_date,
        end_validity_date=law.end_validity_date,
        notification_date=law.notification_date,
        document_type=law.document_type,
        document_type_label=law.document_type_label,
        oj_series_label=law.oj_series_label,
        team_relevancy_classification=_convert_team_relevancy_with_citations_from_json(
            law.team_relevancy_classification
        ),
        has_relevancy=law.has_relevancy,
    )


def legalact_to_law(
    legal_act: LegalAct, *, discovered_at: datetime, law_id: str
) -> Law:
    """Convert Pydantic LegalAct to ORM Law."""
    return Law(
        law_id=law_id,
        title=legal_act.title,
        expression_url=legal_act.expression_url,
        pdf_url=legal_act.pdf_url,
        publication_date=legal_act.publication_date,
        document_date=legal_act.document_date,
        effect_date=legal_act.effect_date,
        end_validity_date=legal_act.end_validity_date,
        notification_date=legal_act.notification_date,
        discovered_at=discovered_at,
        status=LawStatus.RAW,
        category=Category.OPEN,
        eurovoc_labels=legal_act.eurovoc_labels,
        document_type=legal_act.document_type,
        document_type_label=legal_act.document_type_label or DocumentTypeLabel.UNKNOWN,
        oj_series_label=legal_act.oj_series_label or OfficialJournalSeries.UNKNOWN,
        team_relevancy_classification=[],
        has_relevancy=None,
    )


def lawdata_to_law(law_data: LawData) -> Law:
    """Convert Pydantic LawData to ORM Law."""
    return Law(
        law_id=law_data.law_file_id,
        title=law_data.title,
        expression_url=law_data.expression_url,
        pdf_url=law_data.pdf_url,
        publication_date=law_data.publication_date,
        document_date=law_data.document_date,
        effect_date=law_data.effect_date,
        end_validity_date=law_data.end_validity_date,
        notification_date=law_data.notification_date,
        discovered_at=law_data.discovered_at,
        status=law_data.status,
        category=law_data.category,
        law_text=law_data.law_text,
        eurovoc_labels=law_data.eurovoc_labels,
        document_type=law_data.document_type,
        document_type_label=law_data.document_type_label or DocumentTypeLabel.UNKNOWN,
        oj_series_label=law_data.oj_series_label or OfficialJournalSeries.UNKNOWN,
        team_relevancy_classification=_convert_team_relevancy_with_citations_to_json(
            law_data.team_relevancy_classification
        ),
        has_relevancy=law_data.has_relevancy,
    )


def _extract_subject_matter_from_json(
    subject_matter_json: Optional[dict],
) -> Optional[str]:
    """Extract subject matter text from JSON structure."""
    if not subject_matter_json:
        return None

    # Try to extract scope_subject_matter_summary field
    if isinstance(subject_matter_json, dict):
        return subject_matter_json.get("scope_subject_matter_summary")

    return None


def _convert_team_relevancy_from_json(
    team_relevancy_json: List[dict],
) -> List[TeamRelevancy]:
    if not team_relevancy_json:
        return []

    result = []
    for item in team_relevancy_json:
        if isinstance(item, dict):
            result.append(
                TeamRelevancy(
                    team_name=item.get("team_name", ""),
                    is_relevant=item.get("is_relevant", False),
                    reasoning=item.get("reasoning", ""),
                )
            )
    return result


def _convert_team_relevancy_with_citations_from_json(
    team_relevancy_with_citations: list[dict],
) -> List[TeamRelevancyWithCitations]:
    if not team_relevancy_with_citations:
        return []

    result = []
    for item in team_relevancy_with_citations:
        if isinstance(item, dict):
            result.append(
                TeamRelevancyWithCitations(
                    team_name=item.get("team_name", ""),
                    is_relevant=item.get("is_relevant", False),
                    reasoning=item.get("reasoning", ""),
                    citations=item.get("citations", []),
                    error=item.get("error", None),
                )
            )
    return result


def _convert_team_relevancy_with_citations_to_json(
    team_relevancy_with_citations: list[TeamRelevancyWithCitations],
) -> list[dict]:
    """Convert team relevancy with citations from Pydantic models to JSON."""
    if not team_relevancy_with_citations:
        return []
    return [
        team_relevancy.model_dump() for team_relevancy in team_relevancy_with_citations
    ]
