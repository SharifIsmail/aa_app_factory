from dataclasses import asdict
from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger
from sqlalchemy import and_, case, func, select
from sqlalchemy.sql import Select

from service.core.database.models import Law, Team
from service.core.database.postgres_repository import PostgresRepository
from service.law_core.models import LawSummaryData
from service.models import (
    Category,
    DepartmentCount,
    EurovocDescriptorCount,
    LawStatus,
    OfficialJournalSeries,
)


class LawsDAO:
    """Data Access Object for Law table operations."""

    def __init__(self, repo: PostgresRepository) -> None:
        self.repo = repo

    def get(self, law_id: str) -> Optional[Law]:
        """Get a law by its ID."""
        with self.repo.session_scope() as session:
            return session.get(Law, law_id)

    def exists(self, law_id: str) -> bool:
        """Check if a law exists by its ID."""
        with self.repo.session_scope() as session:
            return session.get(Law, law_id) is not None

    def list_by_status(self, status: LawStatus, *, limit: int = 100) -> List[Law]:
        """List laws by status with optional limit."""
        with self.repo.session_scope() as session:
            return session.query(Law).filter(Law.status == status).limit(limit).all()

    def get_oldest_raw_law(self) -> Optional[Law]:
        """Get the oldest RAW law for processing."""
        with self.repo.session_scope() as session:
            return (
                session.query(Law)
                .filter(Law.status == LawStatus.RAW)
                .order_by(Law.discovered_at.asc())
                .first()
            )

    def get_stuck_processing_laws(self, timeout_hours: int = 1) -> List[Law]:
        """Get laws that have been stuck in PROCESSING status."""
        cutoff_time = datetime.now() - timedelta(hours=timeout_hours)
        with self.repo.session_scope() as session:
            return (
                session.query(Law)
                .filter(
                    and_(
                        Law.status == LawStatus.PROCESSING,
                        Law.start_processing < cutoff_time,
                    )
                )
                .all()
            )

    def upsert(self, law: Law) -> None:
        """Insert or update a law."""
        with self.repo.session_scope() as session:
            session.merge(law)

    def mark_processing(self, law_id: str) -> None:
        """Mark a law as processing."""
        with self.repo.session_scope() as session:
            law = session.get(Law, law_id)
            if law:
                law.status = LawStatus.PROCESSING
                law.start_processing = datetime.now()

    def mark_processed(self, law_id: str, html_report_path: str, law_text: str) -> None:
        """Mark a law as processed with report path and law text."""
        with self.repo.session_scope() as session:
            law = session.get(Law, law_id)
            if law:
                law.status = LawStatus.PROCESSED
                law.completed_at = datetime.now()
                law.html_report_path = html_report_path
                law.law_text = law_text

    def mark_failed(self, law_id: str, reason: str) -> None:
        """Mark a law as failed with reason."""
        with self.repo.session_scope() as session:
            law = session.get(Law, law_id)
            if law:
                law.status = LawStatus.FAILED
                law.failure_count = (law.failure_count or 0) + 1
                law.last_failure_at = datetime.now()
                law.last_failure_reason = reason

    def get_status_counts(self) -> dict[str, int]:
        """Get count of laws by status."""
        with self.repo.session_scope() as session:
            counts = session.query(Law.status, func.count()).group_by(Law.status).all()
            return {status.value: count for status, count in counts}

    def get_failure_counts(self) -> dict[str, int]:
        """Get count of laws by failure count."""
        with self.repo.session_scope() as session:
            counts = (
                session.query(Law.failure_count, func.count())
                .group_by(Law.failure_count)
                .all()
            )
            return {str(failure_count or 0): count for failure_count, count in counts}

    def list_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Law]:
        """List laws by publication date range."""
        with self.repo.session_scope() as session:
            query = session.query(Law)

            if start_date:
                query = query.filter(Law.publication_date >= start_date)
            if end_date:
                query = query.filter(Law.publication_date <= end_date)

            return query.order_by(Law.publication_date.desc()).limit(limit).all()

    def select_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Select[tuple[Law]]:
        """Build a selectable for laws by publication date range (for DB pagination)."""
        stmt = select(Law)
        if start_date:
            stmt = stmt.where(Law.publication_date >= start_date)
        if end_date:
            stmt = stmt.where(Law.publication_date <= end_date)
        return stmt.order_by(Law.publication_date.desc(), Law.law_id.desc())

    def count_laws(self) -> int:
        """Count the number of laws."""
        with self.repo.session_scope() as session:
            return session.query(Law).count()

    def search_by_title(self, title_query: str, limit: int = 100) -> List[Law]:
        """Search laws by title containing the query string."""
        with self.repo.session_scope() as session:
            return (
                session.query(Law)
                .filter(Law.title.ilike(f"%{title_query}%"))
                .limit(limit)
                .all()
            )

    def get_all_eurovoc_descriptors(self) -> List[str]:
        """Get all unique eurovoc descriptors."""
        with self.repo.session_scope() as session:
            # Get all non-null eurovoc_labels arrays
            results = (
                session.query(Law.eurovoc_labels)
                .filter(Law.eurovoc_labels.isnot(None))
                .all()
            )

            # Flatten the arrays and get unique values
            descriptors = set()
            for (eurovoc_labels,) in results:
                if eurovoc_labels:
                    descriptors.update(eurovoc_labels)

            return sorted(list(descriptors))

    def update_law_fields(self, law_id: str, update_fields: dict) -> Optional[Law]:
        """Update specific fields of a law."""
        with self.repo.session_scope() as session:
            # Direct update query - more efficient
            result = (
                session.query(Law).filter(Law.law_id == law_id).update(update_fields)
            )
            if result > 0:
                session.commit()
                return session.get(Law, law_id)
            return None

    def get_daily_human_decision_timeline(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        journal_series: Optional[OfficialJournalSeries] = None,
    ) -> list[dict]:
        """Return daily human decision counts grouped by day."""
        with self.repo.session_scope() as session:
            day_expr = func.date_trunc("day", Law.publication_date).label("day")
            relevant_sum = func.sum(
                case((Law.category == Category.RELEVANT, 1), else_=0)
            ).label("relevant")
            not_relevant_sum = func.sum(
                case((Law.category == Category.NOT_RELEVANT, 1), else_=0)
            ).label("not_relevant")
            awaiting_sum = func.sum(
                case((Law.category == Category.OPEN, 1), else_=0)
            ).label("awaiting_decision")
            legal_acts = func.count(Law.law_id).label("legal_acts")

            query = session.query(
                day_expr, relevant_sum, not_relevant_sum, awaiting_sum, legal_acts
            )

            if start_date is not None:
                query = query.filter(Law.publication_date >= start_date)
            if end_date is not None:
                query = query.filter(Law.publication_date <= end_date)
            if journal_series is not None:
                query = query.filter(Law.oj_series_label == journal_series)

            rows = query.group_by(day_expr).order_by(day_expr).all()

        return [
            {
                "date": day,
                "relevant": int(relevant or 0),
                "not_relevant": int(not_relevant or 0),
                "awaiting_decision": int(awaiting or 0),
                "legal_acts": int(legal_acts or 0),
            }
            for (day, relevant, not_relevant, awaiting, legal_acts) in rows
        ]

    def persist_summary(
        self, law_id: str, summary_data: LawSummaryData, html_path: str
    ) -> None:
        """Persist law summary data to the database."""

        # compute has_relevancy efficiently from summary_data.team_relevancy_classification
        has_relevancy: Optional[bool] = None
        try:
            classifications = summary_data.team_relevancy_classification or []
            for item in classifications:
                # items are dicts; guard defensively
                if isinstance(item, dict) and bool(item.get("is_relevant")):
                    has_relevancy = True
                    break
            if has_relevancy is None:
                # if we had classification items but none relevant, set False
                has_relevancy = False if classifications else None
        except Exception as e:
            has_relevancy = None
            logger.error(
                f"Error computing has_relevancy from team_relevancy_classification for law_id: {law_id}. Error: {e}"
            )

        payload = {
            "header_raw": summary_data.header_raw,
            "subject_matter": asdict(summary_data.subject_matter)
            if summary_data.subject_matter
            else None,
            "timeline": asdict(summary_data.timeline)
            if summary_data.timeline
            else None,
            "roles_penalties": asdict(summary_data.roles_penalties)
            if summary_data.roles_penalties
            else None,
            "roles_raw": summary_data.roles_raw,
            "team_relevancy_classification": summary_data.team_relevancy_classification,
            "has_relevancy": has_relevancy,
            "report_generated_at": datetime.now(),
            "html_report_path": html_path,
            "business_areas_affected": summary_data.business_areas_affected,
            "source_link": summary_data.source_link,
            "full_report_link": summary_data.full_report_link,
        }
        self.update_law_fields(law_id, payload)

    def get_department_relevance_counts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        journal_series: Optional[OfficialJournalSeries] = None,
    ) -> tuple[List[DepartmentCount], int]:
        """Get count of relevant legal acts per department within date range.

        Returns:
            tuple: (department_counts_list, total_relevant_acts)
                - department_counts_list: List of dicts with department and relevant_acts count
                - total_relevant_acts: Total unique legal acts with relevancy (no double counting)
        """
        with self.repo.session_scope() as session:
            # Build the base query for laws that have relevancy (more efficient filter)
            query = session.query(Law).filter(
                and_(
                    Law.status == LawStatus.PROCESSED,
                    Law.has_relevancy
                    == True,  # Only laws with at least one relevant team
                    Law.team_relevancy_classification.isnot(None),
                )
            )

            # Apply date filters
            if start_date is not None:
                query = query.filter(Law.publication_date >= start_date)
            if end_date is not None:
                query = query.filter(Law.publication_date <= end_date)
            if journal_series is not None:
                query = query.filter(Law.oj_series_label == journal_series)

            laws: List[Law] = query.all()

            # Get all teams to create department mapping
            teams_query = session.query(Team.name, Team.department).all()
            team_to_department = {
                name.lower().strip(): department for name, department in teams_query
            }

            # Count relevant acts per department
            department_counts: dict[str, int] = {}

            for law in laws:
                teams_with_relevance = law.team_relevancy_classification or []
                relevant_departments = set()

                # Check each team's relevance classification
                for team_relevancy in teams_with_relevance:
                    if isinstance(team_relevancy, dict) and team_relevancy.get(
                        "is_relevant"
                    ):
                        team_name = team_relevancy.get("team_name", "").lower().strip()
                        if team_name in team_to_department:
                            department = team_to_department[team_name]
                            relevant_departments.add(department)

                # Count this law for each relevant department (avoid double counting)
                for department in relevant_departments:
                    department_counts[department] = (
                        department_counts.get(department, 0) + 1
                    )

            # Convert to list of dicts sorted by count (descending)
            result: List[DepartmentCount] = [
                DepartmentCount(department=dept, relevant_acts=count)
                for dept, count in department_counts.items()
            ]
            result.sort(key=lambda x: x.relevant_acts, reverse=True)

            # Return both department counts and total unique relevant acts
            total_relevant_acts = len(
                laws
            )  # laws already filtered to has_relevancy=True
            return result, total_relevant_acts

    def get_eurovoc_descriptor_counts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        journal_series: Optional[OfficialJournalSeries] = None,
    ) -> List[EurovocDescriptorCount]:
        """Get frequency count of EuroVoc descriptors within date range.

        Returns:
            List of dicts with descriptor and frequency count, sorted by frequency (descending)
        """
        with self.repo.session_scope() as session:
            query = session.query(Law).filter(
                and_(
                    Law.status == LawStatus.PROCESSED,
                    Law.eurovoc_labels.isnot(None),
                )
            )

            # Apply date filters
            if start_date is not None:
                query = query.filter(Law.publication_date >= start_date)
            if end_date is not None:
                query = query.filter(Law.publication_date <= end_date)
            if journal_series is not None:
                query = query.filter(Law.oj_series_label == journal_series)

            laws: List[Law] = query.all()

            # Count descriptor frequencies
            descriptor_counts: dict[str, int] = {}

            for law in laws:
                eurovoc_labels = law.eurovoc_labels

                if not isinstance(eurovoc_labels, list) or not eurovoc_labels:
                    continue

                for descriptor in eurovoc_labels:
                    if descriptor and isinstance(descriptor, str):
                        descriptor_counts[descriptor] = (
                            descriptor_counts.get(descriptor, 0) + 1
                        )

            result: List[EurovocDescriptorCount] = [
                EurovocDescriptorCount(descriptor=descriptor, frequency=count)
                for descriptor, count in descriptor_counts.items()
            ]
            result.sort(key=lambda x: x.frequency, reverse=True)

            return result
