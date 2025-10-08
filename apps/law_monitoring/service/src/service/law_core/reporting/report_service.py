"""Report generation service for law analysis results."""

from datetime import UTC, datetime
from typing import Any

from loguru import logger

from service.law_core.artifacts.generators.base_generator import BaseReportGenerator
from service.law_core.artifacts.generators.html_generator import HTMLReportGenerator
from service.law_core.artifacts.generators.pdf_generator import PDFReportGenerator
from service.law_core.artifacts.generators.word_generator import WordReportGenerator
from service.law_core.background_work.workers_constants import REPORTS_FOLDER
from service.law_core.models import (
    LawSummaryData,
    ReportPaths,
    RolesPenalties,
    SubjectMatter,
    TaskStatus,
    Timeline,
    WorkLog,
)
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.law_core.summary.summary_work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.law_core.utils.text_utils import format_date_for_display
from service.models import TeamRelevancyWithCitations


class ReportService:
    """Handles generation and storage of law analysis reports in multiple formats."""

    def __init__(self) -> None:
        """Initialize the report service with storage backend."""
        self.storage_backend = get_configured_storage_backend()

    def _build_law_summary_data(
        self,
        act_id: str,
        work_log: WorkLog,
        header_response: str,
        subject_matter: SubjectMatter,
        timeline_response: Timeline,
        combined_display_data: str,
        roles_penalties: RolesPenalties,
        pdf_url: str,
        team_relevancy_classification: list[TeamRelevancyWithCitations],
        metadata: dict[str, Any] | None = None,
    ) -> LawSummaryData:
        """Build the LawSummaryData object from various data sources."""
        return LawSummaryData(
            law_id=act_id,
            source_link=pdf_url,
            title=metadata.get("title", f"Law Analysis Report for {act_id}")
            if metadata
            else f"Law Analysis Report for {act_id}",
            metadata={
                "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
                **(metadata or {}),
            },
            processing_status=work_log.status.value,
            header_raw=header_response,
            subject_matter=subject_matter,
            timeline=timeline_response,
            roles_penalties=roles_penalties,
            roles_raw=combined_display_data,
            team_relevancy_classification=[
                team.model_dump() for team in team_relevancy_classification
            ],
            document_type_label=metadata.get("document_type_label", "N/A")
            if metadata
            else "N/A",
            oj_series_label=metadata.get("oj_series_label", "N/A")
            if metadata
            else "N/A",
            business_areas_affected=", ".join(metadata.get("eurovoc_labels", []))
            if metadata and metadata.get("eurovoc_labels")
            else "N/A",
            publication_date=format_date_for_display(metadata.get("publication_date"))
            if metadata
            else None,
            document_date=format_date_for_display(metadata.get("document_date"))
            if metadata
            else None,
            end_validity_date=format_date_for_display(metadata.get("end_validity_date"))
            if metadata
            else None,
            notification_date=format_date_for_display(metadata.get("notification_date"))
            if metadata
            else None,
            date_of_effect=format_date_for_display(metadata.get("effect_date"))
            if metadata
            else None,
        )

    def _generate_and_save_report(
        self,
        generator: BaseReportGenerator,
        law_summary_data: LawSummaryData,
        file_extension: str,
    ) -> str | None:
        """Generate and save a single report, handling errors gracefully."""
        act_id = law_summary_data.law_id
        report_type = file_extension.upper()
        try:
            content = generator.render(law_summary_data)
            if not isinstance(content, (str, bytes)):
                logger.error(
                    f"Report generator for {report_type} returned unsupported content type: {type(content).__name__}"
                )
                return None

            filename = f"act_{act_id}.{file_extension}"
            report_path = self.storage_backend.save_file(
                REPORTS_FOLDER, filename, content
            )
            if report_path:
                logger.info(f"{report_type} report saved to: {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"Failed to generate {report_type} report: {e}")
            return None

    def generate_reports(
        self,
        act_id: str,
        work_log: WorkLog,
        header_response: str,
        subject_matter: SubjectMatter,
        timeline_response: Timeline,
        combined_display_data: str,
        roles_penalties: RolesPenalties,
        pdf_url: str,
        team_relevancy_classification: list[TeamRelevancyWithCitations],
        metadata: dict[str, Any] | None = None,
    ) -> ReportPaths:
        """Generate all report formats and return their file paths.

        Args:
            act_id: Unique identifier for the law
            work_log: WorkLog instance for tracking progress
            header_response: Header information
            subject_matter: Extraction results
            timeline_response: Timeline information
            combined_display_data: Combined roles and penalties display data
            roles_penalties: Roles and penalties extraction results
            pdf_url: Source PDF URL
            team_relevancy_classification: Team relevancy classifications
            metadata: Optional metadata for enhanced information

        Returns:
            ReportPaths: Object containing paths to generated reports
        """
        logger.info("Generating law summary reports")
        update_task_status(work_log, TaskKeys.GENERATE_REPORT, TaskStatus.IN_PROGRESS)

        law_summary_data = self._build_law_summary_data(
            act_id,
            work_log,
            header_response,
            subject_matter,
            timeline_response,
            combined_display_data,
            roles_penalties,
            pdf_url,
            team_relevancy_classification,
            metadata,
        )

        report_paths = ReportPaths()

        # Generate HTML content (critical - must succeed)
        try:
            html_generator = HTMLReportGenerator()
            html_content = html_generator.render(law_summary_data)
            filename = f"act_{act_id}.html"
            html_report_path = self.storage_backend.save_file(
                REPORTS_FOLDER, filename, html_content
            )
            if not html_report_path:
                raise RuntimeError(
                    f"HTML report generation failed - storage backend returned empty path for file {filename}"
                )
            report_paths.html = html_report_path
            logger.info("HTML report saved to: {}", report_paths.html)
        except Exception as e:
            logger.error("Failed to generate HTML report: {}", str(e))
            # HTML report is critical - if it fails, we should fail the whole process
            raise RuntimeError(f"Critical HTML report generation failed: {e}") from e

        # Generate other non-critical reports
        report_paths.word = self._generate_and_save_report(
            WordReportGenerator(), law_summary_data, "docx"
        )
        report_paths.pdf = self._generate_and_save_report(
            PDFReportGenerator(), law_summary_data, "pdf"
        )

        logger.info("Law summary reports generated successfully!")
        return report_paths
