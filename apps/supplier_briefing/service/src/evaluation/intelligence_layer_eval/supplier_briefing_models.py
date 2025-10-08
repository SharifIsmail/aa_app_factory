"""
Pydantic models for supplier briefing evaluation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from evaluation.core.pandas_comparator import (
    PandasComparisonConfig,
    PandasComparisonMode,
)


class TextComparisonStatus(str, Enum):
    """Status of text comparison."""

    COMPARED = "compared"
    SKIPPED = "skipped"


class VibeCheckStatus(str, Enum):
    """Status of vibe check for pandas objects."""

    EXACT_MATCH_SKIP = "exact_match_skip"
    NO_OVERLAP_EMPTY_SKIP = "no_overlap_empty_skip"
    LLM_JUDGED = "llm_judged"


class QuestionDifficulty(str, Enum):
    """Difficulty classification of a question."""

    EASY = "Easy"
    HARD = "Hard"


class TextComparisonDetails(BaseModel):
    """Details of text comparison result."""

    status: TextComparisonStatus = Field(
        ..., description="Status of the text comparison"
    )
    reason: str | None = Field(
        default=None, description="Reason for the status (e.g., why skipped)"
    )
    # Additional fields from LLM comparison when status="compared"
    score: float | None = Field(
        default=None, description="Similarity score from LLM comparison"
    )
    explanation: str | None = Field(
        default=None, description="LLM explanation of the comparison"
    )
    specific_differences: list[str] | None = Field(
        default=None, description="List of specific differences found"
    )


class TextComparisonResult(BaseModel):
    """Result of text comparison."""

    is_match: bool = Field(..., description="Whether texts match")
    details: TextComparisonDetails = Field(
        ..., description="Detailed comparison information"
    )


class PandasComparisonResult(BaseModel):
    """Result of pandas objects comparison."""

    score: float = Field(..., description="Similarity score between 0.0 and 1.0")


class VibeCheckResult(BaseModel):
    """Result of pandas objects vibe check."""

    status: VibeCheckStatus = Field(..., description="Status of the vibe check")
    score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    reasoning: str = Field(..., description="Reasoning for the score")


class PandasObjectData(BaseModel):
    """Pandas object data structure."""

    id: str = Field(..., description="Unique identifier for the pandas object")
    pandas_object_json: dict[str, Any] = Field(
        ..., description="JSON format dataframe or series data"
    )


class SupplierBriefingInputDetails(BaseModel):
    """Input details for supplier briefing evaluation."""

    research_question: str = Field(..., description="The research question to evaluate")
    language: str = Field(default="en", description="Language for the research")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    question_difficulty: QuestionDifficulty = Field(
        default=QuestionDifficulty.HARD,
        description=("Difficulty of the example"),
    )
    pandas_comparison_config: PandasComparisonConfig = Field(
        default_factory=lambda: PandasComparisonConfig(
            mode=PandasComparisonMode.EXACT_MATCH
        ),
        description=(
            "Configuration for comparing pandas objects (mode, drop_index, ignore_column_names)"
        ),
    )


class SupplierBriefingOutput(BaseModel):
    """Actual output from supplier briefing system."""

    text: str = Field(..., description="Text response from the system")
    pandas_objects: List[PandasObjectData] = Field(
        default_factory=list, description="Pandas objects from the system"
    )


class SupplierBriefingExpectedOutput(BaseModel):
    """Expected output for supplier briefing evaluation."""

    text: str | None = Field(
        ..., description="Expected text response (None to skip text evaluation)"
    )
    pandas_objects: List[PandasObjectData] = Field(
        default_factory=list, description="Expected pandas objects"
    )


class SupplierBriefingEvaluation(BaseModel):
    """Individual evaluation result for one example."""

    # Core IL evaluation fields
    is_correct: bool = Field(
        ..., description="Whether the prediction matches ground truth"
    )

    # Detailed comparison results from integrated comparison logic
    pandas_objects_score: float = Field(
        ..., description="Similarity score for pandas objects [0.0, 1.0]"
    )
    text_match: bool = Field(..., description="Whether text responses match")

    # Text comparison details
    text_details: Dict[str, Any] = Field(
        default_factory=dict, description="LLM-based text comparison details"
    )

    # Question metadata
    question_id: Optional[str] = Field(None, description="Question identifier")
    research_question: str = Field(..., description="The research question")
    question_difficulty: QuestionDifficulty = Field(
        default=QuestionDifficulty.HARD,
        description="Difficulty of the example",
    )

    # Additional metrics
    has_pandas_objects: bool = Field(
        ..., description="Whether example has pandas objects"
    )
    pandas_objects_count: int = Field(
        default=0, description="Number of pandas objects in result"
    )

    # Vibe check metrics
    vibe_score: float = Field(
        default=0.0, description="LLM-judged dataframe similarity score [0,1]"
    )
    vibe_details: Dict[str, Any] = Field(
        default_factory=dict, description="Details for dataframe vibe check"
    )


class SupplierBriefingAggregation(BaseModel):
    """Aggregated evaluation results across all examples."""

    pass_rate: float = Field(..., description="Overall pass rate (0.0 to 1.0)")

    # Detailed match statistics
    pandas_score: float = Field(
        ..., description="Pandas objects comparison score (0.0 to 1.0)"
    )
    pass_rate_text: float | None = Field(..., description="Text comparison pass rate")
    avg_vibe_score: float = Field(
        default=0.0, description="Average vibe score across examples"
    )
    pass_rate_easy: float | None = Field(
        default=0.0,
        description=(
            "Pass rate computed only over examples with question_difficulty == 'Easy'"
        ),
    )
    pass_rate_hard: float | None = Field(
        default=0.0,
        description=(
            "Pass rate computed only over examples with question_difficulty == 'Hard'"
        ),
    )
