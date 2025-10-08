"""
Law data service for retrieving and updating law data.

This service layer sits between the routes and the database,
providing law-specific business logic for querying and updating law data.
"""

import csv
import io
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from fastapi_pagination import set_page
from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.ext.sqlalchemy import paginate
from filelock import FileLock, Timeout
from loguru import logger

from service.company_config_service import company_config_service
from service.core.database.dependencies import get_laws_dao
from service.core.database.model_adapters import law_to_lawdata
from service.core.database.postgres_repository import create_postgres_repository
from service.dependencies import with_settings
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.models import (
    Category,
    CursorPagination,
    LawData,
    LawDataWithCursorPagination,
)


class LawDataService:
    """Service for querying, retrieving, and updating law data. Thread-safe singleton."""

    # Define which fields can be updated by users
    UPDATABLE_FIELDS = {"category", "status"}

    @staticmethod
    def _law_matches_department_teams(law: LawData, department_teams: set[str]) -> bool:
        """
        Efficiently check if a law is relevant to any team in the department.

        Args:
            law: Law object to check
            department_teams: Set of lowercase team names in the department

        Returns:
            True if law is relevant to any team in the department
        """
        if not law.team_relevancy_classification or not department_teams:
            return False

        for team_relevancy in law.team_relevancy_classification:
            if team_relevancy.is_relevant:
                team_name = team_relevancy.team_name.lower().strip()
                if team_name in department_teams:
                    return True

        return False

    def __init__(self) -> None:
        """Initialize the law query service with database and file locking."""
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        self.laws_dao = get_laws_dao(create_postgres_repository(with_settings()))
        self.storage_backend = get_configured_storage_backend()

        # File locking configuration for thread safety
        self.locks_directory = Path(tempfile.gettempdir()) / "law_data_service_locks"
        self.locks_directory.mkdir(exist_ok=True)
        self._lock_timeout = 0.5  # 500ms timeout to prevent deadlocks

        self._initialized = True

    @contextmanager
    def _with_law_lock(self, law_id: str) -> Generator[None, None, None]:
        """
        Context manager for law-specific operations with cross-process locking.
        Ensures atomic operations on individual law records.

        Args:
            law_id: The ID of the law to lock

        Raises:
            TimeoutError: If lock cannot be acquired within timeout period
        """
        lock_path = self.locks_directory / f"{law_id}.lock"
        lock = FileLock(lock_path, timeout=self._lock_timeout)

        try:
            with lock:
                yield
        except Timeout:
            raise TimeoutError(
                f"Could not acquire lock for law {law_id} within {self._lock_timeout}s"
            )

    def get_available_law_dates(self) -> list[datetime]:
        """
        Get all available law publication dates.

        Returns:
            List of unique publication dates sorted in descending order
        """
        # Get all laws from database
        laws = self.laws_dao.list_by_date_range(limit=10000)

        # Extract unique dates
        dates = set()
        for law in laws:
            if law.publication_date:
                dates.add(law.publication_date.date())

        # Convert to datetime objects and sort
        return sorted(
            [datetime.combine(date, datetime.min.time()) for date in dates],
            reverse=True,
        )

    def get_laws_by_date_range(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> list[LawData]:
        """
        Get laws within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of law data objects within the date range
        """
        laws = self.laws_dao.list_by_date_range(start_date, end_date)

        # Convert to LawData and enrich
        law_data_list = []
        for law in laws:
            law_data = law_to_lawdata(law)
            law_data_list.append(law_data)

        return law_data_list

    def get_laws_cursor_paginated(
        self,
        cursor_params: CursorParams,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> LawDataWithCursorPagination:
        stmt = self.laws_dao.select_by_date_range(start_date, end_date)
        set_page(CursorPage[LawData])

        with self.laws_dao.repo.session_scope() as session:
            page_cursor = paginate(
                session,
                stmt,
                cursor_params,
                transformer=lambda items: [law_to_lawdata(law) for law in items],
            )
            return LawDataWithCursorPagination(
                items=page_cursor.items,
                pagination=CursorPagination(
                    total=page_cursor.total,
                    current_page=page_cursor.current_page,
                    current_page_backwards=page_cursor.current_page_backwards,
                    previous_page=page_cursor.previous_page,
                    next_page=page_cursor.next_page,
                ),
            )

    def get_total_laws(self) -> int:
        """
        Get the total number of laws.

        Returns:
            Total number of laws
        """
        return self.laws_dao.count_laws()

    def search_laws_by_title(
        self,
        title_query: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Search laws by title containing the query string.

        Args:
            title_query: Query string to search for in titles
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of matching law data objects
        """
        laws = self.laws_dao.search_by_title(title_query)

        # Filter by date range if specified
        if start_date or end_date:
            filtered_laws = []
            for law in laws:
                if start_date and law.publication_date < start_date:
                    continue
                if end_date and law.publication_date > end_date:
                    continue
                filtered_laws.append(law)
            laws = filtered_laws

        # Convert to LawData and enrich
        law_data_list = []
        for law in laws:
            law_data = law_to_lawdata(law)
            law_data_list.append(law_data)

        return law_data_list

    def search_laws_by_document_type(
        self,
        document_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Search laws by document type.

        Args:
            document_type: Document type to search for
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of matching law data objects
        """
        laws = self.laws_dao.list_by_date_range(start_date, end_date, limit=10000)

        # Filter by document type
        filtered_laws = []
        for law in laws:
            if (
                law.document_type_label
                and document_type.lower() in law.document_type_label.value.lower()
            ):
                filtered_laws.append(law)

        # Convert to LawData and enrich
        law_data_list = []
        for law in filtered_laws:
            law_data = law_to_lawdata(law)
            law_data_list.append(law_data)

        return law_data_list

    def search_laws_by_journal_series(
        self,
        journal_series: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Search laws by Official Journal series.

        Args:
            journal_series: Journal series to search for
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of matching law data objects
        """
        laws = self.laws_dao.list_by_date_range(start_date, end_date, limit=10000)

        # Filter by journal series
        filtered_laws = []
        for law in laws:
            if (
                law.oj_series_label
                and journal_series.lower() in law.oj_series_label.value.lower()
            ):
                filtered_laws.append(law)

        # Convert to LawData and enrich
        law_data_list = []
        for law in filtered_laws:
            law_data = law_to_lawdata(law)
            law_data_list.append(law_data)

        return law_data_list

    def search_laws_by_eurovoc(
        self,
        eurovoc_descriptors: list[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Search laws by Eurovoc descriptors.

        Args:
            eurovoc_descriptors: List of Eurovoc descriptors to search for
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of matching law data objects
        """
        laws = self.laws_dao.list_by_date_range(start_date, end_date, limit=10000)

        # Filter by eurovoc descriptors
        filtered_laws = []
        for law in laws:
            if law.eurovoc_labels:
                # Check if any of the search descriptors match any of the law's eurovoc labels
                for descriptor in eurovoc_descriptors:
                    if any(
                        descriptor.lower() in label.lower()
                        for label in law.eurovoc_labels
                    ):
                        filtered_laws.append(law)
                        break

        # Convert to LawData and enrich
        law_data_list = []
        for law in filtered_laws:
            law_data = law_to_lawdata(law)
            law_data_list.append(law_data)

        return law_data_list

    def search_laws_by_department(
        self,
        department: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Search laws that are relevant to teams in a specific department.
        Optimized with caching and efficient filtering.

        Args:
            department: Department name to search for
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of matching law data objects
        """
        department_teams = company_config_service.get_department_teams_mapping(
            department
        )

        if not department_teams:
            logger.info(f"No teams found for department '{department}'")
            return []

        laws = self.laws_dao.list_by_date_range(start_date, end_date, limit=10000)
        law_data_list = [
            law_to_lawdata(law)
            for law in laws
            if self._law_matches_department_teams(law_to_lawdata(law), department_teams)
        ]
        logger.info(
            f"Department search for '{department}' found {len(law_data_list)} laws from {len(department_teams)} teams"
        )
        return law_data_list

    def get_all_eurovoc_descriptors(self) -> list[str]:
        """
        Get all unique Eurovoc descriptors from all laws.

        Returns:
            List of unique Eurovoc descriptors
        """
        return self.laws_dao.get_all_eurovoc_descriptors()

    def update_law_data(
        self, law_id: str, update_fields: Dict[str, Any]
    ) -> tuple[bool, Optional[LawData]]:
        """
        Update law data with the provided fields.

        Args:
            law_id: The ID of the law to update
            update_fields: Dictionary of fields to update

        Returns:
            Tuple of (success, updated_law_data)
        """
        with self._with_law_lock(law_id):
            try:
                # Validate updatable fields
                invalid_fields = set(update_fields.keys()) - self.UPDATABLE_FIELDS
                if invalid_fields:
                    logger.warning(
                        f"Attempted to update non-updatable fields {invalid_fields} for law {law_id}"
                    )
                    return False, None

                # Update the law
                updated_law = self.laws_dao.update_law_fields(law_id, update_fields)

                if updated_law:
                    law_data = law_to_lawdata(updated_law)
                    logger.info(
                        f"Successfully updated law {law_id} with fields: {update_fields}"
                    )
                    return True, law_data
                else:
                    logger.warning(f"Law {law_id} not found for update")
                    return False, None

            except Exception as e:
                logger.error(f"Failed to update law {law_id}: {e}")
                return False, None

    def _find_law_by_id(self, law_id: str) -> tuple[Optional[LawData], Optional[str]]:
        """
        Find a law by its ID.

        Args:
            law_id: The ID of the law to find

        Returns:
            Tuple of (law_data, error_message)
        """
        try:
            law = self.laws_dao.get(law_id)
            if law:
                law_data = law_to_lawdata(law)
                return law_data, None
            else:
                return None, f"Law with ID {law_id} not found"
        except Exception as e:
            logger.error(f"Error finding law {law_id}: {e}")
            return None, f"Error retrieving law: {str(e)}"

    def get_laws_by_category(
        self,
        category: Category,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Get all laws filtered by category within an optional date range.

        Args:
            category: The category to filter by
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            List of LawData objects matching the category filter
        """
        try:
            # Get all laws in the date range
            all_laws = self.get_laws_by_date_range(start_date, end_date)

            # Filter by category
            filtered_laws = [law for law in all_laws if law.category == category]

            logger.info(
                f"Found {len(filtered_laws)} laws with category {category.value}"
            )
            return filtered_laws

        except Exception as e:
            logger.error(f"Error retrieving laws by category {category.value}: {e}")
            return []

    def get_laws_evaluated(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[LawData]:
        """
        Get all laws that have been human-evaluated (Category not OPEN),
        optionally filtered by a date range.

        Args:
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            List of LawData objects where category is RELEVANT or NOT_RELEVANT
        """
        try:
            all_laws = self.get_laws_by_date_range(start_date, end_date)
            evaluated = [
                law
                for law in all_laws
                if law.category in {Category.RELEVANT, Category.NOT_RELEVANT}
            ]
            logger.info(f"Found {len(evaluated)} human-evaluated laws (non-OPEN)")
            return evaluated
        except Exception as e:
            logger.error(f"Error retrieving evaluated laws: {e}")
            return []

    def generate_laws_csv(
        self,
        category: Category,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> io.StringIO:
        """
        Generate a CSV export of laws filtered by category.

        Args:
            category: The category to filter by
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            StringIO buffer containing the CSV data
        """
        try:
            # Get laws matching the criteria
            laws = self.get_laws_by_category(category, start_date, end_date)

            # Define CSV fieldnames with human-readable headers
            fieldnames = [
                "Publication Date",
                "Title",
                "Document Type",
                "Official Journal Series",
                "EUR-Lex URL",
                "PDF URL",
                "Effect Date",
                "End Validity Date",
                "Teams Relevant For",
                "Teams Not Relevant For",
                "Category",
                "Status",
            ]

            # Create CSV buffer
            buffer = io.StringIO()
            writer = csv.DictWriter(
                buffer, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
            )
            writer.writeheader()

            # Write law data rows
            for law in laws:
                self._write_csv_row(writer, law)

            buffer.seek(0)
            return buffer

        except Exception as e:
            logger.error(f"Error generating CSV for category {category.value}: {e}")
            # Return empty CSV with headers on error
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=["error"], quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerow({"error": f"Error generating CSV: {str(e)}"})
            buffer.seek(0)
            return buffer

    def generate_evaluated_laws_csv(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> io.StringIO:
        """
        Generate a CSV export of all human-evaluated laws (Category RELEVANT or NOT_RELEVANT).

        Args:
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            StringIO buffer containing the CSV data
        """
        try:
            laws = self.get_laws_evaluated(start_date, end_date)

            fieldnames = [
                "Publication Date",
                "Title",
                "Document Type",
                "Official Journal Series",
                "EUR-Lex URL",
                "PDF URL",
                "Effect Date",
                "End Validity Date",
                "Teams Relevant For",
                "Teams Not Relevant For",
                "Category",
                "Status",
            ]

            buffer = io.StringIO()
            writer = csv.DictWriter(
                buffer, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
            )
            writer.writeheader()

            for law in laws:
                self._write_csv_row(writer, law)

            buffer.seek(0)
            return buffer

        except Exception as e:
            logger.error(f"Error generating evaluated CSV: {e}")
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=["error"], quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerow({"error": f"Error generating evaluated CSV: {str(e)}"})
            buffer.seek(0)
            return buffer

    def _write_csv_row(self, writer: csv.DictWriter, law: LawData) -> None:
        relevant_teams: list[str] = []
        not_relevant_teams: list[str] = []

        if law.team_relevancy_classification:
            for team in law.team_relevancy_classification:
                if team.is_relevant:
                    relevant_teams.append(team.team_name)
                else:
                    not_relevant_teams.append(team.team_name)

        writer.writerow(
            {
                "Publication Date": law.publication_date.date()
                if law.publication_date
                else "",
                "Title": law.title,
                "Document Type": law.document_type_label.value
                if law.document_type_label
                else "",
                "Official Journal Series": law.oj_series_label.value
                if law.oj_series_label
                else "",
                "EUR-Lex URL": law.expression_url,
                "PDF URL": law.pdf_url,
                "Effect Date": law.effect_date.date() if law.effect_date else "",
                "End Validity Date": law.end_validity_date.date()
                if law.end_validity_date
                else "",
                "Teams Relevant For": "; ".join(relevant_teams),
                "Teams Not Relevant For": "; ".join(not_relevant_teams),
                "Category": law.category.value if law.category else "",
                "Status": law.status.value if law.status else "",
            }
        )
