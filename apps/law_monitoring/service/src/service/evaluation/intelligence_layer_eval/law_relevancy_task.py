import uuid
from typing import List

from loguru import logger
from pharia_inference_sdk.core import Task, TaskSpan
from pydantic import BaseModel, Field

from service.law_core.law_report_service import LawReportService
from service.law_core.summary.summary_work_log_manager import create_work_log
from service.models import (
    RelevancyClassifierLegalActInput,
    TeamRelevancy,
)


class LawRelevancyInputDetails(BaseModel):
    """Input details for law relevancy evaluation."""

    law_text: str = Field(..., description="The full text of the law to evaluate")
    law_title: str = Field(..., description="The title of the law")
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the law"
    )


class LawRelevancyTask(Task[LawRelevancyInputDetails, List[TeamRelevancy]]):
    """Task to evaluate the relevancy of a law for a company's teams."""

    def do_run(
        self, input: LawRelevancyInputDetails, task_span: TaskSpan
    ) -> List[TeamRelevancy]:
        """Execute the law relevancy evaluation."""

        # Generate a unique ID for this evaluation
        eval_id = f"eval_{uuid.uuid4().hex[:8]}"

        # Create a mock work log for the evaluation
        work_log = create_work_log(work_log_id=eval_id)

        # Initialize the law report service
        law_report_service = LawReportService(act_id=eval_id, work_log=work_log)

        subject_matter = law_report_service.summarize_subject_matter(input.law_text)

        # Classify relevancy directly with full law text
        team_relevancy = law_report_service.classify_relevancy(
            RelevancyClassifierLegalActInput(
                full_text=input.law_text,
                title=input.law_title,
                summary=subject_matter.scope_subject_matter_summary,
                url=input.metadata["expression_url"],
            )
        )

        # Check for any errors during classification and fail task if any are found
        errors = [team.error for team in team_relevancy if team.error]
        if errors:
            raise RuntimeError(f"Relevancy classification failed with errors: {errors}")

        logger.info(f"Successfully evaluated relevancy for {len(team_relevancy)} teams")
        return team_relevancy
