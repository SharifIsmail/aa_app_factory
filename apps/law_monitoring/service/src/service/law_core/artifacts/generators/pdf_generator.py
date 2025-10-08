"""
PDF Generator for Law Summary Reports

This module provides functionality to generate PDF reports from law summary data
using ReportLab for professional document creation.
"""

import html
import re
from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from service.law_core.models import LawSummaryData
from service.models import OfficialJournalSeries

from .base_generator import BaseReportGenerator


class PDFReportGenerator(BaseReportGenerator):
    """
    PDF report generator for law summary reports.

    Uses ReportLab to create professional PDF documents with styled content,
    tables, and proper formatting for law analysis data.
    """

    def __init__(self) -> None:
        """Initialize the PDF generator."""
        super().__init__()

    def render(self, law_summary_data: LawSummaryData) -> bytes:
        """
        Render law summary data as PDF document matching HTML template structure exactly.

        Args:
            law_summary_data: Structured law summary analysis data

        Returns:
            bytes: PDF document content
        """
        # Create a BytesIO buffer to store the PDF
        buffer = BytesIO()

        # Create the PDF document with modern margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=60,
        )

        # Get default styles and create custom ones matching HTML template
        styles = getSampleStyleSheet()

        # Main title style - smaller and cleaner
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=14,  # Much smaller
            fontName="Helvetica-Bold",
            spaceAfter=16,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),
            lineHeight=1.4,  # More spacing between lines
        )

        # Metadata style - same size as body text
        metadata_style = ParagraphStyle(
            "Metadata",
            parent=styles["Normal"],
            fontSize=12,
            fontName="Helvetica",
            spaceAfter=8,
            spaceBefore=4,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),
        )

        # Section header style - only slightly larger than body
        section_header_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading1"],
            fontSize=14,  # Much smaller - minimal hierarchy
            fontName="Helvetica-Bold",
            spaceAfter=8,
            spaceBefore=16,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),
            borderWidth=0,
            borderPadding=0,
        )

        # Content style with much more spacing
        content_style = ParagraphStyle(
            "Content",
            parent=styles["Normal"],
            fontSize=12,
            fontName="Helvetica",
            spaceAfter=12,  # Increased
            spaceBefore=12,  # Increased
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),
            lineHeight=2.0,  # Much more line spacing
            allowOrphans=0,
            allowWidows=0,
        )

        # Info value style - same as body text
        info_value_style = ParagraphStyle(
            "InfoValue",
            parent=styles["Normal"],
            fontSize=12,  # Same as body text
            fontName="Helvetica",
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),
        )

        # Simple alert style without colors
        alert_style = ParagraphStyle(
            "Alert",
            parent=styles["Normal"],
            fontSize=12,
            fontName="Helvetica",
            spaceAfter=8,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),  # Simple black
        )

        # Simple table header style
        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontSize=12,
            fontName="Helvetica-Bold",
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),  # Black text
        )

        # Simple table cell style
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=11,
            fontName="Helvetica",
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),  # Black text
            lineHeight=1.5,
        )

        # Subsection heading style - same as section headers
        subsection_style = ParagraphStyle(
            "Subsection",
            parent=styles["Normal"],
            fontSize=14,  # Same as section headers
            fontName="Helvetica-Bold",
            spaceAfter=8,
            spaceBefore=16,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#000000"),
        )

        # Build the document content matching HTML structure exactly
        story = []

        # REPORT HEADER SECTION - Keep title and metadata together
        title_text = law_summary_data.title
        header_elements = []

        header_elements.append(Paragraph(title_text, title_style))
        header_elements.append(Spacer(1, 12))

        # Published date
        if law_summary_data.publication_date:
            header_elements.append(
                Paragraph(
                    f"Published: {law_summary_data.publication_date}", metadata_style
                )
            )

        # Generated at metadata
        generated_at = law_summary_data.metadata.get(
            "generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        header_elements.append(
            Paragraph(f"Generated at: {generated_at}", metadata_style)
        )

        # Law ID metadata
        if law_summary_data.law_id:
            header_elements.append(
                Paragraph(f"Law ID: {law_summary_data.law_id}", metadata_style)
            )

        # Keep the entire header together on one page
        story.append(KeepTogether(header_elements))

        story.append(Spacer(1, 32))  # More spacing between sections

        # BASIC INFORMATION SECTION - matching HTML template structure exactly
        story.append(Paragraph("Basic Information", section_header_style))

        # Create clean info items without unnecessary tables - matching HTML template structure
        if law_summary_data.document_date:
            story.extend(
                self._create_info_item(
                    "DOCUMENT DATE",
                    str(law_summary_data.document_date),
                    info_value_style,
                )
            )
        else:
            story.extend(
                self._create_info_item(
                    "DOCUMENT DATE",
                    "",
                    info_value_style,
                )
            )

        if law_summary_data.publication_date:
            story.extend(
                self._create_info_item(
                    "PUBLICATION DATE",
                    str(law_summary_data.publication_date),
                    info_value_style,
                )
            )
        else:
            story.extend(
                self._create_info_item(
                    "PUBLICATION DATE",
                    "Not explicitly stated",
                    info_value_style,
                )
            )

        if law_summary_data.date_of_effect:
            story.extend(
                self._create_info_item(
                    "DATE OF EFFECT",
                    str(law_summary_data.date_of_effect),
                    info_value_style,
                )
            )
        else:
            story.extend(
                self._create_info_item(
                    "DATE OF EFFECT",
                    "Not explicitly stated",
                    info_value_style,
                )
            )

        if law_summary_data.end_validity_date:
            story.extend(
                self._create_info_item(
                    "END OF VALIDITY",
                    str(law_summary_data.end_validity_date),
                    info_value_style,
                )
            )
        else:
            story.extend(
                self._create_info_item(
                    "END OF VALIDITY",
                    "Not explicitly stated",
                    info_value_style,
                )
            )

        if law_summary_data.document_type_label:
            story.extend(
                self._create_info_item(
                    "DOCUMENT TYPE",
                    str(law_summary_data.document_type_label),
                    info_value_style,
                )
            )

        oj_series_label = law_summary_data.oj_series_label
        if oj_series_label and str(oj_series_label) != OfficialJournalSeries.UNKNOWN:
            story.extend(
                self._create_info_item(
                    "JOURNAL SERIES",
                    str(oj_series_label),
                    info_value_style,
                )
            )

        if law_summary_data.business_areas_affected:
            story.extend(
                self._create_info_item(
                    "BUSINESS AREAS AFFECTED",
                    str(law_summary_data.business_areas_affected),
                    info_value_style,
                )
            )

        revenue_penalties_from_subject = (
            law_summary_data.subject_matter.revenue_based_penalties or "N/A"
        )
        story.extend(
            self._create_info_item(
                "REVENUE-BASED PENALTIES",
                revenue_penalties_from_subject,
                info_value_style,
            )
        )

        key_stakeholder_roles = (
            law_summary_data.subject_matter.key_stakeholder_roles or "N/A"
        )
        story.extend(
            self._create_info_item(
                "KEY STAKEHOLDER ROLES",
                key_stakeholder_roles,
                info_value_style,
            )
        )

        if law_summary_data.source_link:
            story.extend(
                self._create_info_item_with_link(
                    "SOURCE LINK",
                    "View Original Document",
                    law_summary_data.source_link,
                    info_value_style,
                )
            )

        story.append(Spacer(1, 32))  # More spacing between sections

        # SUBJECT MATTER SECTION - Keep header with content
        subject_elements = [Paragraph("Subject Matter", section_header_style)]
        # Use scope_subject_matter_summary from the structured object
        subject_content = law_summary_data.subject_matter.scope_subject_matter_summary
        if subject_content:
            content = self._process_content(subject_content)
            subject_elements.append(self._create_content_box(content, content_style))
        story.append(KeepTogether(subject_elements))
        story.append(Spacer(1, 32))  # More spacing between sections

        # ROLES, RESPONSIBILITIES AND PENALTIES SECTION
        story.append(
            Paragraph("Roles, Responsibilities and Penalties", section_header_style)
        )
        story.append(Spacer(1, 20))  # Add vertical space after section title

        # Revenue-Based Penalties Alert with red background for YES
        revenue_status = law_summary_data.roles_penalties.revenue_based_penalties_status
        if revenue_status:
            alert_text = f"<b>Revenue-Based Penalties: {revenue_status}</b>"
            if revenue_status.upper() == "YES":
                alert_text += "<br/>This law includes penalties calculated as a percentage of company revenue/turnover."
                # Use red background for YES status
                story.append(
                    self._create_alert_box(alert_text, alert_style, is_danger=True)
                )
            else:
                # Use normal styling for other statuses
                story.append(Paragraph(alert_text, alert_style))
            story.append(Spacer(1, 12))

        # Roles table (matching HTML table structure)
        if law_summary_data.roles_raw:
            roles_table = self._create_roles_table(
                law_summary_data.roles_raw, table_header_style, table_cell_style
            )
            if roles_table:
                story.append(roles_table)

        # General Penalties subsection
        if (
            law_summary_data.roles_penalties.general_penalties_raw
            and law_summary_data.roles_penalties.general_penalties_raw.strip()
        ):
            story.append(
                Paragraph("General Penalties Not Role-Specific", subsection_style)
            )
            content = self._process_content(
                law_summary_data.roles_penalties.general_penalties_raw
            )
            story.append(self._create_content_box(content, content_style))

        # Penalty Severity Assessment subsection
        if (
            law_summary_data.roles_penalties.penalty_severity_assessment_raw
            and law_summary_data.roles_penalties.penalty_severity_assessment_raw.strip()
        ):
            story.append(Paragraph("Penalty Severity Assessment", subsection_style))
            content = self._process_content(
                law_summary_data.roles_penalties.penalty_severity_assessment_raw
            )
            story.append(self._create_content_box(content, content_style))

        story.append(Spacer(1, 32))  # More spacing between sections

        # TIMELINE FOR COMPLIANCE SECTION - Keep header with content (moved to end as per HTML)
        timeline_elements = [Paragraph("Timeline for Compliance", section_header_style)]
        if law_summary_data.timeline.timeline_content:
            content = self._process_content(law_summary_data.timeline.timeline_content)
            timeline_elements.append(self._create_content_box(content, content_style))
        story.append(KeepTogether(timeline_elements))
        story.append(Spacer(1, 20))

        # ADDITIONAL RESOURCES SECTION (if present)
        if law_summary_data.full_report_link:
            story.append(Paragraph("Additional Resources", section_header_style))
            story.append(
                self._create_content_box("Download Full PDF Report", content_style)
            )

        # Build the PDF
        doc.build(story)

        # Get the PDF content
        buffer.seek(0)
        return buffer.getvalue()

    def _process_content(self, content: str) -> str:
        """
        Process content by transforming markers to bold formatting for ReportLab.

        Args:
            content: Raw content string

        Returns:
            str: Processed content with HTML formatting for ReportLab
        """
        if not content:
            return ""

        # Transform =text= markers to bold with line breaks
        content = self._transform_markers_to_bold(content)

        # Clean up HTML entities
        import html

        content = html.unescape(content)

        # Fix ReportLab compatibility: ensure <br/> tags are self-closing and properly formatted
        content = content.replace("<br>", "<br/>")
        content = content.replace("<BR>", "<br/>")

        # Remove any <para> tags that might conflict with <br/> tags
        content = content.replace("<para>", "").replace("</para>", "")
        content = content.replace("<PARA>", "").replace("</PARA>", "")

        return content

    @staticmethod
    def _create_info_item(label: str, value: str, value_style: Any) -> list[Any]:
        """
        Create a clean info item without unnecessary tables or backgrounds.

        Args:
            label: Label text
            value: Value text
            value_style: Style for value

        Returns:
            List: Simple paragraph elements
        """
        return [Paragraph(f"<b>{label}:</b> {value}", value_style), Spacer(1, 8)]

    def _create_info_item_with_link(
        self, label: str, text: str, url: str, value_style: Any
    ) -> list[Any]:
        """
        Create a clean info item with a hyperlink.

        Args:
            label: Label text
            text: Link text to display
            url: URL to link to
            value_style: Style for value

        Returns:
            List: Simple paragraph elements with hyperlink
        """
        # Create HTML hyperlink for ReportLab with underline
        hyperlink_html = (
            f'<b>{label}:</b> <a href="{url}" color="blue"><u>{text}</u></a>'
        )
        return [Paragraph(hyperlink_html, value_style), Spacer(1, 8)]

    @staticmethod
    def _create_content_box(content: str, style: Any) -> Any:
        """
        Create clean content without unnecessary backgrounds or tables.

        Args:
            content: Content text
            style: Paragraph style

        Returns:
            Paragraph: Simple paragraph with clean styling
        """
        return Paragraph(content, style)

    def _create_roles_table(
        self, roles_raw: str, header_style: Any, cell_style: Any
    ) -> Any:
        """
        Create roles table matching HTML table structure exactly.

        Args:
            roles_raw: Raw roles data
            header_style: Style for headers
            cell_style: Style for cells

        Returns:
            Table: Formatted roles table
        """
        if not roles_raw:
            return None

        # Parse roles data (matching HTML template logic)
        table_data = []

        # Add table headers
        table_data.append(
            [
                Paragraph("Role", header_style),
                Paragraph("Responsibilities", header_style),
                Paragraph("Penalties", header_style),
            ]
        )

        # Parse role lines (matching HTML template logic)
        for line in roles_raw.split("\n"):
            if "|" in line and line.strip() and not line.startswith("="):
                parts = line.split("|")
                if len(parts) >= 3:
                    table_data.append(
                        [
                            Paragraph(parts[0].strip(), cell_style),
                            Paragraph(
                                self._process_content(parts[1].strip()), cell_style
                            ),
                            Paragraph(
                                self._process_content(parts[2].strip()), cell_style
                            ),
                        ]
                    )
                elif len(parts) == 2:
                    # Fallback for legacy 2-column format
                    table_data.append(
                        [
                            Paragraph(parts[0].strip(), cell_style),
                            Paragraph(
                                self._process_content(parts[1].strip()), cell_style
                            ),
                            Paragraph("", cell_style),
                        ]
                    )

        if len(table_data) <= 1:  # Only headers, no data
            return None

        # Create clean table with minimal styling
        table = Table(table_data, colWidths=[1.8 * inch, 2.6 * inch, 1.8 * inch])

        # Clean, print-friendly table styling
        table_styles = [
            # Simple header styling - bold text, no background waste
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#000000")),
            # Clean cell styling
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#000000")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 11),
            # Minimal borders - just what's needed
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            # Clean spacing
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]

        table.setStyle(TableStyle(table_styles))

        return table

    def _clean_html_content(self, content: str) -> str:
        """
        Clean HTML content by removing tags and converting to plain text.

        Args:
            content: HTML content string

        Returns:
            str: Clean text content
        """
        if not content:
            return ""

        # Remove HTML tags
        content = re.sub(r"<[^>]+>", "", content)

        # Convert all HTML entities using standard library function
        content = html.unescape(content)

        # Clean up extra whitespace
        content = re.sub(r"\s+", " ", content)
        content = content.strip()

        return content

    def _transform_markers_to_bold(self, text: str) -> str:
        """
        Transform =text= markers to bold section titles AND handle line breaks properly.

        Args:
            text: Text with =...= markers and bullet points

        Returns:
            str: Text with proper HTML formatting for ReportLab
        """
        if not text:
            return ""

        # First, convert all newlines to <br/> to preserve line breaks
        text = text.replace("\n", "<br/>")

        # Convert bullet points to have proper spacing
        text = text.replace("<br/>- ", "<br/><br/>- ")

        # Now handle =Section= markers
        # Split text by =markers= and rebuild with proper formatting
        parts = re.split(r"=([^=]+)=", text)
        result = ""

        # parts[0] is text before first marker (if any)
        if parts[0].strip():
            result += parts[0].strip()

        # Process pairs: marker_text, content_after_marker
        for i in range(1, len(parts), 2):
            if i < len(parts):
                marker_text = parts[i]
                content_after = parts[i + 1] if i + 1 < len(parts) else ""

                # Add line breaks and bold marker
                if result:  # Add spacing if not first item
                    result += "<br/><br/>"
                result += f"<b>{marker_text}</b><br/>"

                # Add content after marker
                if content_after.strip():
                    result += content_after.strip()

        # Clean up multiple consecutive <br/> tags
        result = re.sub(r"(<br/>){3,}", "<br/><br/>", result)

        # Clean up leading <br/> tags
        result = re.sub(r"^(<br/>)+", "", result)

        return result

    def _parse_bold_text(self, text: str) -> str:
        """
        Parse bold text markers - they're already in HTML format from _transform_markers_to_bold.

        Args:
            text: Text that may contain HTML bold tags and line breaks

        Returns:
            str: Text ready for ReportLab
        """
        if not text:
            return ""

        # Text is already in correct HTML format from _transform_markers_to_bold
        # Just ensure any remaining **text** patterns are converted
        text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

        return text

    def _wrap_url(self, url: str, max_chars: int = 45) -> str:
        """
        Wrap long URLs by inserting line breaks at appropriate points.

        Args:
            url: URL to wrap
            max_chars: Maximum characters per line

        Returns:
            str: URL with line breaks
        """
        if not url or len(url) <= max_chars:
            return url

        # Break URL at natural separators
        result = ""
        current_line = ""

        i = 0
        while i < len(url):
            char = url[i]
            current_line += char

            # Check if we should break after this character
            should_break = False

            # If line is getting long and we're at a natural break point
            if len(current_line) >= max_chars:
                # Break after these characters
                if char in ["/", "?", "&", "=", "-", "_"] and i < len(url) - 1:
                    should_break = True
                # Break before these characters if next is one
                elif i + 1 < len(url) and url[i + 1] in ["/", "?", "&", "="]:
                    should_break = True

            if should_break:
                result += current_line + "\n"
                current_line = ""

            i += 1

        # Add remaining characters
        if current_line:
            result += current_line

        return result

    def _wrap_text(self, text: str, max_chars: int = 60) -> str:
        """
        Wrap long text by inserting line breaks at appropriate points.

        Args:
            text: Text to wrap
            max_chars: Maximum characters per line

        Returns:
            str: Text with line breaks
        """
        if not text or len(text) <= max_chars:
            return text

        # Split long text into multiple lines
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def _create_alert_box(
        self, alert_text: str, style: Any, is_danger: bool = False
    ) -> Any:
        """
        Create a simple alert with optional red background for danger alerts.

        Args:
            alert_text: Alert text with HTML formatting
            style: Paragraph style
            is_danger: Whether to use red background styling (for Revenue-Based Penalties: YES)

        Returns:
            Paragraph or Table: Alert with appropriate styling
        """
        if is_danger:
            # Create red background styling for YES revenue-based penalties
            danger_style = ParagraphStyle(
                "DangerAlert",
                parent=style,
                fontSize=12,
                fontName="Helvetica",
                spaceAfter=16,  # More spacing after
                spaceBefore=16,  # More spacing before
                alignment=TA_LEFT,
                textColor=colors.HexColor("#ef4444"),  # Red text
                backColor=colors.HexColor("#fee2e2"),  # Light red background
                borderColor=colors.HexColor("#ef4444"),  # Red border
                borderWidth=1,
                borderPadding=16,  # More internal padding
                leftIndent=4,  # Small red left border effect
            )
            return Paragraph(alert_text, danger_style)
        else:
            return Paragraph(alert_text, style)
