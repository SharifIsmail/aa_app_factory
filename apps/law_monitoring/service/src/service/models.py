from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from service.dependencies import with_settings
from service.law_core.chunker.models import DocumentChunk

settings = with_settings()


class LawStatus(str, Enum):
    """Enum for law processing status values."""

    RAW = "RAW"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Category(str, Enum):
    """Enum for user-defined law categorization."""

    OPEN = "OPEN"
    RELEVANT = "RELEVANT"
    NOT_RELEVANT = "NOT_RELEVANT"


class DocumentTypeLabel(str, Enum):
    """Enum for document type values."""

    DIRECTIVE = "Directive"
    REGULATION = "Regulation"
    JUDICIAL_INFORMATION = "Judicial information"
    DECISION = "Decision"
    ANNOUNCEMENT = "Announcements"
    RATE = "Exchange rate"
    NOTICE = "Notice"
    CORRIGENDUM = "Corrigendum"
    IMPLEMENTING_DECISION = "Implementing decision"
    IMPLEMENTING_REGULATION = "Implementing regulation"
    SUMMARY = "Summary"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class OfficialJournalSeries(str, Enum):
    """Enum for Official Journal series values."""

    L_SERIES = "L-Series"  # Legislation - legally binding acts
    C_SERIES = "C-Series"  # Communication - non-binding documents
    UNKNOWN = "Unknown"

    @classmethod
    def from_eur_lex_uri(cls, oj_series_uri: Optional[str]) -> "OfficialJournalSeries":
        """
        Map EUR-Lex OJ series URI to enum value.
        Args:
            oj_series_uri: URI from EUR-Lex (e.g., 'http://publications.europa.eu/resource/authority/document-collection/OJ-L')
        Returns:
            OfficialJournalSeries enum value
        """
        if not oj_series_uri:
            return cls.UNKNOWN

        if "OJ-L" in oj_series_uri:
            return cls.L_SERIES
        elif "OJ-C" in oj_series_uri:
            return cls.C_SERIES
        else:
            return cls.UNKNOWN


class HealthResponse(BaseModel):
    status: Literal["ok"]


class QuoteResponse(BaseModel):
    quote: str


class LegalAct(BaseModel):
    """Representation of legal acts fetched from EUR-Lex with metadata.
    Used for external API responses and data exchange."""

    # Core identifiers
    expression_url: str = Field(description="URI of the work")
    title: str = Field(default="N/A", description="Title of the legal act")
    pdf_url: str = Field(
        default="", description="URL to the PDF version of the legal act"
    )

    # Classifications
    eurovoc_labels: Optional[List[str]] = Field(
        default=None,
        description="Eurovoc classification labels",
    )

    # Document type identification
    document_type: Optional[str] = Field(
        default=None,
        description="Document type URI (directive, regulation, etc.)",
    )
    document_type_label: Optional[DocumentTypeLabel] = Field(
        default=DocumentTypeLabel.UNKNOWN,
        description="Human-readable document type label",
    )

    # Official Journal series identification
    oj_series_label: Optional[OfficialJournalSeries] = Field(
        default=OfficialJournalSeries.UNKNOWN,
        description="Official Journal series (L=Legislation, C=Communication)",
    )

    publication_date: datetime = Field(
        description="Publication date in the Official Journal"
    )
    # Multiple date fields from the enhanced query
    document_date: Optional[datetime] = Field(
        default=None, description="Date of the document"
    )
    effect_date: Optional[datetime] = Field(
        default=None, description="Date when the legal act comes into effect"
    )
    end_validity_date: Optional[datetime] = Field(
        default=None, description="Date when the legal act ends validity"
    )
    notification_date: Optional[datetime] = Field(
        default=None, description="Notification date"
    )

    # Backward compatibility - use publication_date as default date
    @property
    def date(self) -> Optional[datetime]:
        """Backward compatibility property for date field."""
        return self.publication_date


class LegalActsResponse(BaseModel):
    """Response model for legal acts query."""

    legal_acts: list[LegalAct] = Field(description="List of legal acts found")
    total_count: int = Field(description="Total number of legal acts found")
    start_date: datetime = Field(description="Start date of the query range")
    end_date: datetime = Field(description="End date of the query range")


class LegalActsRequest(BaseModel):
    """Request model for legal acts query."""

    start_date: datetime = Field(description="Start date for the query (YYYY-MM-DD)")
    end_date: datetime = Field(description="End date for the query (YYYY-MM-DD)")
    limit: int = Field(
        default=1000, ge=1, le=10000, description="Maximum number of results per day"
    )


class TeamDescription(BaseModel):
    name: str
    description: str
    department: str
    daily_processes: list[str]
    relevant_laws_or_topics: str


class CompanyConfig(BaseModel):
    """Internal model for company configuration data."""

    company_description: str | None = Field(
        default=None, description="Company description text"
    )
    teams: List[TeamDescription] = Field(
        default_factory=list, description="List of team descriptions"
    )


class ApplicationConfig(BaseModel):
    """Internal model to configure aspects of the application"""

    enable_engage_partner_button: bool = Field(
        default=settings.enable_partner_button,
        description="Flag indicating if partner engagement button is visible or not",
    )


class RelevancyClassifierLegalActInput(BaseModel):
    """Input model for law relevancy classification."""

    full_text: str = Field(..., description="Full text of the law to evaluate")
    title: str = Field(..., description="Title of the law")
    url: str = Field(..., description="URL of the law to evaluate")
    summary: str = Field(..., description="Summary of the law to evaluate")


class Relevancy(BaseModel):
    is_relevant: bool
    reasoning: str


class Factfulness(BaseModel):
    """Represents the factfulness of a global reasoning for a given chunk. Justifies with a local reasoning."""

    is_factual: bool
    local_reasoning: str


class CitationToolInput(BaseModel):
    """Input model for citation tool. Contains information to ground a global reasoning back to a chunk."""

    global_reasoning: str
    chunk: DocumentChunk
    legal_act: Optional[RelevancyClassifierLegalActInput] = None
    team_profile: Optional[TeamDescription] = None


class Citation(BaseModel):
    """Represents the factfulness of a global reasoning for a given chunk. Justifies with a local reasoning."""

    chunk: DocumentChunk
    factfulness: Factfulness


class TeamRelevancy(BaseModel):
    """Output of the relevancy classifier for a given team."""

    team_name: str
    is_relevant: bool  # Global Relevancy - connects a legal act with the team profile (team_name)
    reasoning: str  # Global Reasoning - provides justification of why legal act is relevant to team profile (team_name)
    error: Optional[str] = None


class TeamRelevancyWithCitations(TeamRelevancy):
    """Final output result of relevancy classification and citation steps for a given team and legal act."""

    # Citations (original doc chunks) - evidence supporting the global reasoning
    citations: list[Citation] | None = None
    error: Optional[str] = None

    @classmethod
    def from_team_relevancy(
        cls, team_relevancy: TeamRelevancy, citations: list[Citation]
    ) -> "TeamRelevancyWithCitations":
        return cls(
            team_name=team_relevancy.team_name,
            is_relevant=team_relevancy.is_relevant,
            reasoning=team_relevancy.reasoning,
            citations=citations,
            error=team_relevancy.error,
        )


class LawData(BaseModel):
    """Model representing law data exactly as stored in backend.
    Includes processing status and enrichments for internal business logic
    such as user categorization, and relevancy assessment."""

    title: str
    expression_url: str
    pdf_url: str
    publication_date: datetime
    discovered_at: datetime
    law_file_id: str
    law_text: str | None = None
    status: LawStatus
    subject_matter_text: str | None = (
        None  # Contains subject matter summary extracted from JSON reports for PROCESSED laws
    )
    category: Category = Field(
        default=Category.OPEN, description="User's categorization of the law"
    )
    # Enhanced metadata fields
    eurovoc_labels: Optional[List[str]] = Field(
        default=None,
        description="Eurovoc classification labels",
    )
    document_date: Optional[datetime] = Field(
        default=None, description="Date of the document"
    )
    effect_date: Optional[datetime] = Field(
        default=None, description="Date when the legal act comes into effect"
    )
    end_validity_date: Optional[datetime] = Field(
        default=None, description="Date when the legal act ends validity"
    )
    notification_date: Optional[datetime] = Field(
        default=None, description="Notification date"
    )
    # Document type identification fields
    document_type: Optional[str] = Field(
        default=None,
        description="Document type URI (directive, regulation, etc.)",
    )
    document_type_label: Optional[DocumentTypeLabel] = Field(
        default=DocumentTypeLabel.UNKNOWN,
        description="Human-readable document type label",
    )

    # Official Journal series identification fields
    oj_series_label: Optional[OfficialJournalSeries] = Field(
        default=OfficialJournalSeries.UNKNOWN,
        description="Official Journal series (L=Legislation, C=Communication)",
    )
    team_relevancy_classification: List[TeamRelevancyWithCitations] = Field(
        default_factory=list, description="Relevancy assessment for each team"
    )
    has_relevancy: bool | None = Field(
        default=None,
        description="True if any team has is_relevant == True; None if unset",
    )


class Pagination(BaseModel):
    """Pagination information."""

    total_items: int = Field(description="Total number of law data items")


class CursorPagination(BaseModel):
    """Cursor pagination information."""

    total: int = Field(description="Total number of law data items")
    current_page: str = Field(description="Current page cursor")
    current_page_backwards: str = Field(description="Current page backwards cursor")
    previous_page: str | None = Field(description="Previous page cursor")
    next_page: str | None = Field(description="Next page cursor")


class LawDataWithPagination(BaseModel):
    """Law data with pagination."""

    law_data: list[LawData] = Field(description="The law data")
    pagination: Pagination = Field(description="Pagination information")


class LawDataWithCursorPagination(BaseModel):
    """Law data with cursor pagination."""

    items: list[LawData] = Field(description="The law data")
    pagination: CursorPagination = Field(description="Pagination information")


class DepartmentCount(BaseModel):
    """Type definition for department relevance count result."""

    department: str = Field(description="Department name")
    relevant_acts: int = Field(description="Number of relevant acts for the department")


class EurovocDescriptorCount(BaseModel):
    """Type definition for EuroVoc descriptor frequency count result."""

    descriptor: str = Field(description="EuroVoc descriptor name")
    frequency: int = Field(description="Frequency of the descriptor")
