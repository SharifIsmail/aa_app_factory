"""Main law summary service that orchestrates the entire analysis workflow."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any, Dict

from loguru import logger

from service.company_config_service import company_config_service
from service.core.database.dependencies import get_laws_dao
from service.core.database.postgres_repository import create_postgres_repository
from service.dependencies import with_settings
from service.law_core.chunker.models import DocumentChunk
from service.law_core.chunker.paragraphchunker import ParagraphChunker
from service.law_core.extraction.law_processor import LawProcessor
from service.law_core.models import (
    LawSummaryData,
    RolesPenalties,
    SubjectMatter,
    TaskStatus,
    Timeline,
    WorkLog,
)
from service.law_core.relevancy_classification.citation_tool import (
    LLMCitationTool,
)
from service.law_core.relevancy_classification.relevancy_classifier_full_text import (
    RelevancyClassifierFullText,
)
from service.law_core.reporting.report_service import ReportService
from service.law_core.summary.model_tools_manager import (
    REPO_EXTRACTED_DATA,
    initialize_model,
    initialize_tools,
)
from service.law_core.summary.summary_work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.law_core.utils.text_utils import (
    combine_roles_and_penalties_for_display,
    format_date_for_display,
)
from service.models import (
    Citation,
    RelevancyClassifierLegalActInput,
    TeamRelevancy,
    TeamRelevancyWithCitations,
)
from service.task_execution import is_cancelled


class LawReportService:
    """Main service for law analysis and summary generation."""

    def __init__(self, act_id: str, work_log: WorkLog):
        self.act_id = act_id
        self.work_log = work_log

        self.tools = self._initialize_extraction_tools()
        self.llm_completion_tool = self.tools["llm_completion_tool"]

        self.law_processor = LawProcessor(self.llm_completion_tool, work_log)

        self.relevancy_classifier = RelevancyClassifierFullText(
            self.llm_completion_tool,
            work_log,
            company_config_service.get_company_config(),
        )
        self.citation_tool = LLMCitationTool(
            self.llm_completion_tool,
        )
        self.report_service = ReportService()
        self.laws_dao = get_laws_dao(create_postgres_repository(with_settings()))

    def _initialize_extraction_tools(self) -> Dict[str, Any]:
        """Initialize extraction tools."""
        model = initialize_model()

        logger.info("Initializing tools...")
        tools = initialize_tools(model, self.act_id, self.work_log)
        logger.info("Tools initialized successfully")

        if not tools:
            logger.error(
                "Failed to initialize extraction tools - tools returned None/empty"
            )
            raise RuntimeError("Tool initialization failed - tools returned None/empty")

        return tools

    def _setup_law_data(self, expression_url: str, law_text: str) -> None:
        """Setup law data storage."""
        logger.info("Setting up WorkLog data storage with law-specific repositories")

        # Store law data using expression_url for fetching
        self.law_processor.store_law_text(expression_url, law_text)

    def _extract_header_information(
        self, metadata: Dict[str, Any] | None = None
    ) -> str:
        """Extract or build header information from metadata.

        Args:
            metadata: Optional metadata for enhanced information

        Returns:
            str: Header response text
        """
        if metadata:
            header_response = self.law_processor.build_report_header_from_metadata(
                metadata
            )
        else:
            logger.warning(
                "No metadata provided for header information - using placeholder"
            )
            # Create minimal header as fallback
            header_response = f"""=Title=
Law Analysis Report for {self.act_id}

=Effective Date=
N/A

=Document Type=
Legal Act

=Business Areas Affected=
N/A"""

            self.work_log.data_storage.store_to_repo(
                REPO_EXTRACTED_DATA,
                "HEADER",
                {"collapsed": "DONE", "expanded": header_response},
            )

        return header_response

    def summarize_subject_matter(self, law_text: str) -> SubjectMatter:
        """Extract and summarize subject matter from law text.

        Args:
            law_text: The law text content to analyze

        Returns:
            SubjectMatter: Summarized subject matter information

        Raises:
            RuntimeError: If subject matter summarization fails
        """
        try:
            return self.law_processor.summarize_subject_matter(law_text)
        except Exception as e:
            logger.error(f"Exception during subject matter extraction: {e}")
            raise RuntimeError(f"Subject matter extraction failed: {e}") from e

    def classify_relevancy(
        self,
        legal_act: RelevancyClassifierLegalActInput,
    ) -> list[TeamRelevancy]:
        """Classify team relevancy based on law content.

        Args:
            legal_act: data of the legal act to analyze
            metadata: Optional metadata for enhanced information

        Returns:
            list[TeamRelevancyWithChunkRelevancies]: Team relevancy classifications

        Raises:
            RuntimeError: If relevancy classification fails
        """
        try:
            team_relevancy_classification = self.relevancy_classifier.classify(
                legal_act
            )
            logger.info("Relevancy classification completed")

            return team_relevancy_classification

        except Exception as e:
            logger.error(f"Exception during team relevancy classification: {e}")
            raise RuntimeError(f"Team relevancy classification failed: {e}") from e

    def cite(
        self,
        team_relevancy_classification: TeamRelevancy,
        chunks: list[DocumentChunk],
    ) -> list[Citation]:
        return self.citation_tool.cite(team_relevancy_classification, chunks)

    def classify_relevancy_with_citations(
        self,
        legal_act: RelevancyClassifierLegalActInput,
    ) -> list[TeamRelevancyWithCitations]:
        team_relevancy_classification = self.classify_relevancy(legal_act)

        chunker = ParagraphChunker()
        chunks = chunker.chunk_document(legal_act.full_text)

        result = []

        # remember order of teams in classification result
        teams_ordering = [
            relevancy.team_name for relevancy in team_relevancy_classification
        ]

        # citation tool's default workers count is 3 => in total 3x3
        max_workers = 3

        with ThreadPoolExecutor(max_workers=min(len(chunks), max_workers)) as executor:
            cite_processing_tasks = {
                executor.submit(
                    self.cite,
                    team_relevancy,
                    chunks,
                ): team_relevancy
                for team_relevancy in team_relevancy_classification
            }

            # Collect results as they complete, maintaining order by chunk.order_index
            results_by_team_name = {}
            for completed_task in as_completed(cite_processing_tasks):
                team_relevancy = cite_processing_tasks[completed_task]
                citations = completed_task.result()
                results_by_team_name[team_relevancy.team_name] = (
                    TeamRelevancyWithCitations.from_team_relevancy(
                        team_relevancy=team_relevancy, citations=citations
                    )
                )

            # Build result using original teams ordering
            for team_name in teams_ordering:
                if team_name in results_by_team_name:
                    result.append(results_by_team_name[team_name])
                else:
                    raise RuntimeError(
                        f"Team {team_name} not found in citation results"
                    )

        return result

    def _extract_timeline(self, law_text: str) -> Timeline:
        try:
            timeline = self.law_processor.extract_timeline(law_text)
            return timeline
        except Exception as e:
            logger.error(f"Exception during timeline extraction: {e}")
            raise RuntimeError(f"Timeline extraction failed: {e}") from e

    def _extract_roles_and_penalties(self, law_text: str) -> RolesPenalties:
        try:
            roles_penalties = (
                self.law_processor.extract_roles_responsibilities_penalties(law_text)
            )
            return roles_penalties
        except Exception as e:
            logger.error(
                f"Exception during roles/responsibilities/penalties extraction: {e}"
            )
            raise RuntimeError(
                f"Roles/responsibilities/penalties extraction failed: {e}"
            ) from e

    def _generate_final_reports(
        self,
        header_response: str,
        subject_matter: SubjectMatter,
        timeline: Timeline,
        roles_penalties: RolesPenalties,
        pdf_url: str,
        team_relevancy_classification: list[TeamRelevancyWithCitations],
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        # Combine roles and penalties for display (only the matrix part)
        combined_display_data = combine_roles_and_penalties_for_display(
            roles_penalties.compliance_matrix_raw
        )

        try:
            report_paths = self.report_service.generate_reports(
                self.act_id,
                self.work_log,
                header_response,
                subject_matter,
                timeline,
                combined_display_data,
                roles_penalties,
                pdf_url,
                team_relevancy_classification,
                metadata,
            )
        except Exception as e:
            logger.error(f"Exception during final report generation: {e}")
            raise RuntimeError(f"Final report generation failed: {e}") from e

        # Persist summary data to database
        if report_paths.html:
            try:
                law_summary_data = LawSummaryData(
                    # Core identification
                    law_id=self.act_id,
                    source_link=pdf_url,
                    title=metadata.get(
                        "title", f"Law Analysis Report for {self.act_id}"
                    )
                    if metadata
                    else f"Law Analysis Report for {self.act_id}",
                    metadata={
                        "generated_at": datetime.now(UTC).strftime(
                            "%Y-%m-%d %H:%M:%S UTC"
                        ),
                        **(metadata or {}),
                    },
                    processing_status=self.work_log.status.value,
                    header_raw=header_response,
                    subject_matter=subject_matter,
                    timeline=timeline,
                    roles_penalties=roles_penalties,
                    roles_raw=combined_display_data,
                    # Team relevancy data
                    team_relevancy_classification=[
                        team.model_dump() for team in team_relevancy_classification
                    ],
                    # Basic information fields (from metadata)
                    document_type_label=metadata.get("document_type_label", "N/A")
                    if metadata
                    else "N/A",
                    oj_series_label=metadata.get("oj_series_label", "N/A")
                    if metadata
                    else "N/A",
                    business_areas_affected=", ".join(
                        metadata.get("eurovoc_labels", [])
                    )
                    if metadata and metadata.get("eurovoc_labels")
                    else "N/A",
                    # Optional date fields - with safe date formatting
                    publication_date=format_date_for_display(
                        metadata.get("publication_date")
                    )
                    if metadata
                    else None,
                    document_date=format_date_for_display(metadata.get("document_date"))
                    if metadata
                    else None,
                    end_validity_date=format_date_for_display(
                        metadata.get("end_validity_date")
                    )
                    if metadata
                    else None,
                    notification_date=format_date_for_display(
                        metadata.get("notification_date")
                    )
                    if metadata
                    else None,
                    date_of_effect=format_date_for_display(metadata.get("effect_date"))
                    if metadata
                    else None,
                )

                self.laws_dao.persist_summary(
                    self.act_id, law_summary_data, report_paths.html
                )
                logger.info("Law summary data persisted to database successfully")
            except Exception as e:
                logger.error("Failed to persist summary data to database: {}", str(e))

        extracted_data = self.work_log.data_storage.retrieve_all_from_repo(
            REPO_EXTRACTED_DATA
        )
        self.work_log.data_storage.store_to_repo(
            REPO_EXTRACTED_DATA,
            "extracted_data",
            extracted_data,
        )

        # Store the report path in work_log for later retrieval
        self.work_log.report_file_path = report_paths.html

        update_task_status(
            self.work_log, TaskKeys.GENERATE_REPORT, TaskStatus.COMPLETED
        )
        self.work_log.status = TaskStatus.COMPLETED

        logger.info("Law summary computation completed successfully!")

        return report_paths.html or ""

    def analyze_law_and_generate_report(
        self,
        expression_url: str,
        pdf_url: str,
        law_text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        """Generate a comprehensive law summary by orchestrating all extraction and reporting steps.

        Args:
            expression_url: URL of the law expression
            pdf_url: URL of the PDF document
            law_text: The law text content to analyze
            metadata: Optional metadata for enhanced information

        Returns:
            str: Path to the generated HTML report, or empty string if failed/cancelled
        """
        logger.info("Starting law summary computation")
        logger.info(f"Expression URL: {expression_url}")
        logger.info(f"PDF URL: {pdf_url}")
        logger.info(f"Execution ID: {self.act_id}")

        # Check cancellation before expensive operations
        if is_cancelled(work_log=self.work_log, execution_id=self.act_id):
            return ""

        # Setup law data
        self._setup_law_data(expression_url, law_text)

        # Check cancellation before starting extraction phase
        if is_cancelled(work_log=self.work_log, execution_id=self.act_id):
            return ""

        # Extract header information
        header_response = self._extract_header_information(metadata)

        if is_cancelled(work_log=self.work_log, execution_id=self.act_id):
            return ""

        # Extract subject matter
        subject_matter = self.summarize_subject_matter(law_text)

        def _fallback_title() -> str:
            logger.warning("using fallback title for law report")
            return f"Law Analysis Report for {self.act_id}"

        if not metadata:
            title = _fallback_title()
        else:
            title = metadata.get("title", _fallback_title())

        # Classify relevancy directly with full law text
        team_relevancy_classification = self.classify_relevancy_with_citations(
            RelevancyClassifierLegalActInput(
                title=title,
                full_text=law_text,
                url=expression_url,
                summary=subject_matter.scope_subject_matter_summary,
            )
        )

        # Check cancellation before timeline extraction
        if is_cancelled(work_log=self.work_log, execution_id=self.act_id):
            return ""

        # Extract timeline
        timeline = self._extract_timeline(law_text)

        # Check cancellation before roles and penalties extraction
        if is_cancelled(work_log=self.work_log, execution_id=self.act_id):
            return ""

        # Extract roles and penalties
        roles_penalties = self._extract_roles_and_penalties(law_text)

        # Check cancellation before final report generation
        if is_cancelled(work_log=self.work_log, execution_id=self.act_id):
            return ""

        # Generate final reports
        return self._generate_final_reports(
            header_response,
            subject_matter,
            timeline,
            roles_penalties,
            pdf_url,
            team_relevancy_classification,
            metadata,
        )
