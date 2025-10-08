"""Provider implementation that fetches BaFin materials via RSS + Firecrawl."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable, List

from service.models import DocumentTypeLabel, LegalAct, OfficialJournalSeries

from external_sources.shared.dataset import build_expression_url, ensure_dataset, iter_cached_records

SOURCE_ID = "bafin_firecrawl"
ENDPOINT_ENV_VAR = "MY_PROVIDER_BASE_URL"
DEFAULT_ENDPOINT_BASE_URL = "http://localhost:8000"
FORCE_REFRESH_ENV_VAR = "MY_PROVIDER_FORCE_REFRESH"


def _resolve_endpoint_base_url() -> str:
    """Return the configured base URL for expression links."""
    return os.environ.get(ENDPOINT_ENV_VAR, DEFAULT_ENDPOINT_BASE_URL)


def fetch_legal_acts(
    start_date: datetime,
    end_date: datetime,
    limit: int = 1000,
) -> Iterable[LegalAct]:
    """
    Return legal acts published within the provided interval.

    Args:
        start_date: Inclusive lower bound for ``publication_date``.
        end_date: Inclusive upper bound for ``publication_date``.
        limit: Maximum number of results to return.
    Raises:
        ValueError: If the provided date range or limit are invalid.
    """
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")
    if limit <= 0:
        raise ValueError("limit must be a positive integer")

    base_url = _resolve_endpoint_base_url()
    force_refresh = os.environ.get(FORCE_REFRESH_ENV_VAR, "").lower() in {
        "1",
        "true",
        "yes",
    }
    try:
        dataset = ensure_dataset(force_refresh=force_refresh)
    except Exception as exc:
        raise RuntimeError(f"[{SOURCE_ID}] failed to load BaFin dataset: {exc}") from exc
    acts: List[LegalAct] = []

    for record in iter_cached_records(dataset):
        publication_date = record.publication_datetime
        if publication_date < start_date or publication_date > end_date:
            continue

        document_type_label = _map_document_type(record.document_type)

        acts.append(
            LegalAct(
                expression_url=build_expression_url(base_url, record.identifier),
                title=record.title,
                pdf_url=record.pdf_url,
                eurovoc_labels=list(record.eurovoc_labels) if record.eurovoc_labels else None,
                document_type=record.document_type,
                document_type_label=document_type_label,
                oj_series_label=OfficialJournalSeries.UNKNOWN,
                publication_date=publication_date,
                document_date=None,
                effect_date=None,
                end_validity_date=None,
                notification_date=None,
            )
        )

        if len(acts) >= limit:
            break

    return acts


def _map_document_type(label: str) -> DocumentTypeLabel:
    normalized = (label or "").strip().lower()
    mapping = {
        "directive": DocumentTypeLabel.DIRECTIVE,
        "regulation": DocumentTypeLabel.REGULATION,
        "decision": DocumentTypeLabel.DECISION,
        "notice": DocumentTypeLabel.NOTICE,
        "announcement": DocumentTypeLabel.ANNOUNCEMENT,
        "summary": DocumentTypeLabel.SUMMARY,
        "other": DocumentTypeLabel.OTHER,
    }
    return mapping.get(normalized, DocumentTypeLabel.UNKNOWN)
