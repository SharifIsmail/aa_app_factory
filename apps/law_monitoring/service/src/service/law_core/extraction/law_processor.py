"""Law text extraction service for analyzing legal documents."""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from loguru import logger

from service.law_core.models import (
    RolesPenalties,
    SubjectMatter,
    TaskStatus,
    Timeline,
    WorkLog,
)
from service.law_core.summary.model_tools_manager import (
    REPO_EXTRACTED_DATA,
    REPO_LAW_DATA,
)
from service.law_core.summary.summary_prompts import (
    EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES_PROMPT,
    EXTRACT_SUBJECT_MATTER_PROMPT,
    EXTRACT_TIMELINE_PROMPT,
)
from service.law_core.summary.summary_work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.law_core.utils.text_utils import extract_field, extract_section_content


class LawProcessor:
    """Handles processing and extraction of structured data from law texts using LLM tools."""

    def __init__(self, llm_completion_tool: Any, work_log: WorkLog):
        self.llm_completion_tool = llm_completion_tool
        self.work_log = work_log

    def store_law_text(self, law_url: str, law_text: str) -> None:
        """Store the fetched law text data."""
        logger.info("Setting fetch law task status to IN_PROGRESS")
        update_task_status(self.work_log, TaskKeys.FETCH_LAW, TaskStatus.IN_PROGRESS)

        self.work_log.data_storage.store_to_repo(
            REPO_LAW_DATA,
            "law_text",
            {
                "url": law_url,
                "text": law_text,
                "timestamp": datetime.now().isoformat(),
            },
        )

        update_task_status(self.work_log, TaskKeys.FETCH_LAW, TaskStatus.COMPLETED)
        logger.info("Law text fetched successfully")

    def build_report_header_from_metadata(self, metadata: Dict[str, Any]) -> str:
        logger.info("Building header information from EUR-Lex metadata")
        update_task_status(
            self.work_log, TaskKeys.EXTRACT_HEADER, TaskStatus.IN_PROGRESS
        )

        # Format dates for display
        def format_date(date_val: Any) -> str:
            if date_val is None:
                return "N/A"
            if isinstance(date_val, str):
                try:
                    date_val = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                except:
                    return date_val
            return (
                date_val.strftime("%d.%m.%Y")
                if hasattr(date_val, "strftime")
                else str(date_val)
            )

        # Build header response using metadata
        header_response = f"""=Title=
{metadata.get("title", "N/A")}

=Effective Date=
{format_date(metadata.get("effect_date")) if metadata.get("effect_date") else format_date(metadata.get("publication_date"))}

=Document Type=
{metadata.get("document_type", "EU Legal Act")}

=Business Areas Affected=
{", ".join(metadata.get("eurovoc_labels", [])) if metadata.get("eurovoc_labels") else "N/A"}

=Publication Date=
{format_date(metadata.get("publication_date"))}

=Document Date=
{format_date(metadata.get("document_date"))}

=End Validity Date=
{format_date(metadata.get("end_validity_date"))}

=Notification Date=
{format_date(metadata.get("notification_date"))}"""

        update_task_status(self.work_log, TaskKeys.EXTRACT_HEADER, TaskStatus.COMPLETED)
        self.work_log.data_storage.store_to_repo(
            REPO_EXTRACTED_DATA,
            "HEADER",
            {"collapsed": "DONE", "expanded": header_response},
        )

        return header_response

    def summarize_subject_matter(self, law_text: str) -> SubjectMatter:
        logger.info("Extracting subject matter")
        update_task_status(
            self.work_log, TaskKeys.EXTRACT_SUBJECT_MATTER, TaskStatus.IN_PROGRESS
        )

        subject_matter_prompt = EXTRACT_SUBJECT_MATTER_PROMPT.format(law_text=law_text)
        subject_matter_response = self.llm_completion_tool.forward(
            prompt=subject_matter_prompt, purpose="Extract subject matter"
        ).replace("==========", "")

        # Extract individual components from the response
        key_stakeholder_roles = extract_field(
            subject_matter_response, "Key Stakeholder Roles"
        )
        revenue_based_penalties = extract_field(
            subject_matter_response, "Revenue-Based Penalties"
        )
        scope_subject_matter_summary = extract_field(
            subject_matter_response, "Scope & Subject Matter Summary"
        )

        subject_matter = SubjectMatter(
            key_stakeholder_roles=key_stakeholder_roles,
            revenue_based_penalties=revenue_based_penalties,
            scope_subject_matter_summary=scope_subject_matter_summary,
        )

        update_task_status(
            self.work_log, TaskKeys.EXTRACT_SUBJECT_MATTER, TaskStatus.COMPLETED
        )

        self.work_log.data_storage.store_to_repo(
            REPO_EXTRACTED_DATA,
            "SUBJECT_MATTER",
            {
                "collapsed": "DONE",
                "expanded": subject_matter_response,
                **asdict(subject_matter),
            },
        )
        logger.info("Subject matter extracted successfully")

        return subject_matter

    def extract_timeline(self, law_text: str) -> Timeline:
        logger.info("Extracting timeline and compliance deadlines")
        update_task_status(
            self.work_log, TaskKeys.EXTRACT_TIMELINE, TaskStatus.IN_PROGRESS
        )

        timeline_prompt = EXTRACT_TIMELINE_PROMPT.format(law_text=law_text)
        timeline_response = self.llm_completion_tool.forward(
            prompt=timeline_prompt, purpose="Extract timeline and compliance deadlines"
        ).replace("==========", "")

        timeline = Timeline(timeline_content=timeline_response)

        update_task_status(
            self.work_log, TaskKeys.EXTRACT_TIMELINE, TaskStatus.COMPLETED
        )
        self.work_log.data_storage.store_to_repo(
            REPO_EXTRACTED_DATA,
            "TIMELINE",
            {"collapsed": "DONE", "expanded": timeline_response},
        )
        logger.info("Timeline information extracted successfully")

        return timeline

    def extract_roles_responsibilities_penalties(self, law_text: str) -> RolesPenalties:
        logger.info("Extracting roles, responsibilities and penalties")
        update_task_status(
            self.work_log,
            TaskKeys.EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES,
            TaskStatus.IN_PROGRESS,
        )

        combined_prompt = EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES_PROMPT.format(
            law_text=law_text
        )
        combined_response = self.llm_completion_tool.forward(
            prompt=combined_prompt,
            purpose="Extract roles, responsibilities and penalties",
        ).replace("==========", "")

        # Extract individual sections
        general_penalties_raw = extract_section_content(
            combined_response,
            "GENERAL PENALTIES NOT ROLE-SPECIFIC",
            "Revenue-Based Penalties",
        )
        revenue_based_penalties_status_str = extract_field(
            combined_response, "Revenue-Based Penalties"
        ).upper()

        has_revenue_penalties = False
        if revenue_based_penalties_status_str == "YES":
            has_revenue_penalties = True
        elif revenue_based_penalties_status_str != "NO":
            logger.warning(
                f"Revenue-Based Penalties status is '{revenue_based_penalties_status_str}', "
                f"which is not 'YES' or 'NO'. Interpreting as 'NO'."
            )
            # Defaulted to NO and False if not explicitly YES.

        penalty_severity_assessment_raw = extract_section_content(
            combined_response, "Penalty Severity Assessment", "COMPLIANCE MATRIX"
        )
        compliance_matrix_raw = extract_section_content(
            combined_response, "COMPLIANCE MATRIX"
        )

        roles_penalties = RolesPenalties(
            general_penalties_raw=general_penalties_raw,
            revenue_based_penalties_status=revenue_based_penalties_status_str,
            penalty_severity_assessment_raw=penalty_severity_assessment_raw,
            compliance_matrix_raw=compliance_matrix_raw,
            has_revenue_based_penalties=has_revenue_penalties,
        )

        update_task_status(
            self.work_log,
            TaskKeys.EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES,
            TaskStatus.COMPLETED,
        )

        # Store data for backward compatibility
        self.work_log.data_storage.store_to_repo(
            REPO_EXTRACTED_DATA,
            "ROLES_RESPONSIBILITIES_PENALTIES_FULL_RESPONSE",
            {"collapsed": "DONE", "expanded": combined_response},
        )

        stored_data_for_roles_penalties = {
            "collapsed": "DONE",
            "expanded": combined_response,
            "general_penalties_raw": general_penalties_raw,
            "revenue_based_penalties_status": revenue_based_penalties_status_str,
            "penalty_severity_assessment_raw": penalty_severity_assessment_raw,
            "compliance_matrix_raw": compliance_matrix_raw,
            "has_revenue_based_penalties": has_revenue_penalties,
        }
        self.work_log.data_storage.store_to_repo(
            REPO_EXTRACTED_DATA,
            "ROLES_RESPONSIBILITIES_PENALTIES",
            stored_data_for_roles_penalties,
        )

        logger.info(
            "Roles, responsibilities and penalties extracted successfully. Revenue-based penalties: {}",
            revenue_based_penalties_status_str,
        )

        return roles_penalties
