import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from typing import Tuple

from loguru import logger

from service.law_core.models import TaskStatus, WorkLog
from service.law_core.relevancy_classification.relevancy_classifier import (
    RelevancyClassifier,
)
from service.law_core.relevancy_classification.relevancy_prompts import (
    LEGAL_ACT_TEAM_RELEVANCY_PROMPT,
)
from service.law_core.summary.model_tools_manager import REPO_EXTRACTED_DATA
from service.law_core.summary.summary_work_log_manager import (
    TaskKeys,
    update_task_status,
)
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.models import (
    CompanyConfig,
    RelevancyClassifierLegalActInput,
    TeamDescription,
    TeamRelevancy,
)
from service.task_execution import is_cancelled


class RelevancyClassifierError(Enum):
    """Enum for the relevancy classifier errors."""

    PROCESSING_FAILED = "Processing of relevancy classification failed. Legal act marked relevant as a safety measure."


class RelevancyClassifierFullText(RelevancyClassifier):
    """Classifies the relevancy of legal acts for different teams."""

    def __init__(
        self,
        llm_completion_tool: LLMCompletionTool,
        work_log: WorkLog,
        company_config: CompanyConfig,
        max_retries: int = 2,
    ):
        """Initialize the relevancy classifier.

        Args:
            llm_completion_tool: The LLM completion tool for making queries
            work_log: Work log for progress tracking and data storage
            company_config: CompanyConfig object containing company description and teams
            max_retries: Maximum number of retries if LLM response is malformed
        """
        self.llm_completion_tool = llm_completion_tool
        self.work_log = work_log
        self.company_config = company_config
        self.max_retries = max_retries

    def _get_team_profiles(self) -> list[TeamDescription]:
        """Get team profiles from the company configuration."""
        team_profiles = self.company_config.teams

        if len(team_profiles) == 0:
            logger.warning("No team profiles found in company configuration")
            return []

        return team_profiles

    def _get_company_description(self) -> str | None:
        """Get company description from the company configuration."""
        company_description = self.company_config.company_description

        if not company_description:
            logger.warning("No company description found in company configuration")
            return None

        return company_description

    def _build_prompt(
        self,
        team_profile: TeamDescription,
        law_title: str,
        law_text: str,
        company_description: str,
    ) -> str:
        """Build the prompt for LLM relevancy assessment.

        Args:
            team_profile: TeamDescription object containing team information
            law_title: Title of the legal act
            law_text: Full text of the legal act
            company_description: General company description

        Returns:
            Formatted prompt string
        """
        legal_act = f"TITLE: {law_title}\nFULL TEXT:\n{law_text}"
        team_profile_str = team_profile.model_dump_json(indent=2)

        return LEGAL_ACT_TEAM_RELEVANCY_PROMPT.format(
            legal_act=legal_act,
            company_description=company_description,
            team_profile=team_profile_str,
        )

    def _parse_response(self, raw_response: str) -> Tuple[str, bool | None]:
        """Parse the LLM response to extract reasoning and relevancy decision.

        Args:
            raw_response: Raw response from the LLM

        Returns:
            Tuple of (reasoning, relevancy_bool_or_None)
        """
        if not raw_response:
            return "", None

        decision_match = re.search(
            r"#DECISION:\s*(.*?)(?=#RESULT:|$)", raw_response, re.DOTALL | re.IGNORECASE
        )
        reasoning = decision_match.group(1).strip() if decision_match else ""

        result_match = re.search(r"#RESULT:\s*(YES|NO)", raw_response, re.IGNORECASE)
        if not result_match:
            logger.warning(
                f"Could not parse RESULT from LLM response: {raw_response}..."
            )
            return reasoning, None

        result_str = result_match.group(1).upper()
        is_relevant = result_str == "YES"

        return reasoning, is_relevant

    def _query_llm_and_parse(self, prompt: str, team_name: str) -> TeamRelevancy:
        """Query the LLM and parse the response, with retries for malformed responses.

        Args:
            prompt: The prompt to send to the LLM
            team_name: Name of the team being assessed

        Returns:
            TeamRelevancy object with the assessment results
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Querying LLM for team '{team_name}' (attempt {attempt + 1})"
                )

                raw_response = self.llm_completion_tool.forward(
                    prompt=prompt, purpose=f"Assess relevancy for team: {team_name}"
                )

                reasoning, is_relevant = self._parse_response(raw_response)

                if is_relevant is not None:
                    logger.info(
                        f"Successfully assessed team '{team_name}': {'RELEVANT' if is_relevant else 'NOT RELEVANT'}"
                    )
                    return TeamRelevancy(
                        team_name=team_name,
                        is_relevant=is_relevant,
                        reasoning=reasoning,
                        error=None,
                    )

                logger.warning(
                    f"Failed to parse LLM response for team '{team_name}' on attempt {attempt + 1}"
                )

            except Exception as e:
                logger.error(
                    f"Error querying LLM for team '{team_name}' on attempt {attempt + 1}: {e}"
                )
                last_exception = e
                if attempt == self.max_retries:
                    break

        logger.error(
            f"All retries failed for team '{team_name}', marking as relevant for safe fallback"
        )
        error_message = RelevancyClassifierError.PROCESSING_FAILED.value
        logger.error(f"{error_message}")
        return TeamRelevancy(
            team_name=team_name,
            is_relevant=True,
            reasoning=error_message,
            error=str(last_exception)
            if last_exception
            else "Parsing failed on all retries.",
        )

    def _get_relevancy_for_single_team(
        self,
        team_profile: TeamDescription,
        law_title: str,
        law_text: str,
        company_description: str,
    ) -> TeamRelevancy:
        """Process a single team for relevancy assessment.

        Args:
            team_profile: TeamDescription object containing team information
            law_title: Title of the legal act
            law_text: Full text of the legal act
            company_description: General company description

        Returns:
            TeamRelevancy object with the assessment results
        """
        team_name = team_profile.name
        logger.info(f"Processing team: {team_name}")

        prompt = self._build_prompt(
            team_profile, law_title, law_text, company_description
        )
        return self._query_llm_and_parse(prompt, team_name)

    def classify(
        self, legal_act: RelevancyClassifierLegalActInput
    ) -> list[TeamRelevancy]:
        """Classify the relevancy of a legal act for all teams.

        Args:
            law_data: data of the legal act to classify

        Returns:
            List of TeamRelevancy objects, one for each team
        """
        logger.info(f"Starting relevancy classification for law: {legal_act.title}")

        # Update task status to in progress
        update_task_status(
            self.work_log, TaskKeys.COMPUTE_IMPACT_ON_EACH_TEAM, TaskStatus.IN_PROGRESS
        )

        try:
            if is_cancelled(work_log=self.work_log, execution_id=self.work_log.id):
                logger.info("Relevancy classification cancelled")
                return []

            team_profiles = self._get_team_profiles()
            if len(team_profiles) == 0:
                logger.warning(
                    "No team profiles found, skipping team relevancy classification."
                )
                return []

            company_description = self._get_company_description()
            if company_description is None:
                logger.warning(
                    "No company description found, skipping team relevancy classification."
                )
                return []

            results: list[TeamRelevancy] = []

            # Process teams concurrently using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(len(team_profiles), 5)) as executor:
                # Submit all tasks
                future_to_team = {
                    executor.submit(
                        self._get_relevancy_for_single_team,
                        team_profile,
                        legal_act.title,
                        legal_act.full_text,
                        company_description,
                    ): team_profile
                    for team_profile in team_profiles
                }

                for future in as_completed(future_to_team):
                    # Check for cancellation before processing each result
                    if is_cancelled(
                        work_log=self.work_log, execution_id=self.work_log.id
                    ):
                        logger.info("Cancelling remaining team processing tasks")
                        # Cancel remaining futures
                        for f in future_to_team:
                            f.cancel()
                        return []

                    team_profile = future_to_team[future]

                    try:
                        team_result = future.result()
                        results.append(team_result)
                    except Exception as e:
                        team_name = team_profile.name
                        logger.error(f"Error processing team '{team_name}': {e}")
                        # Add a fallback result for failed teams
                        results.append(
                            TeamRelevancy(
                                team_name=team_name,
                                is_relevant=True,
                                reasoning="Processing of relevancy classification failed. This is marked as relevant as a safety measure.",
                            )
                        )

            results_dict = [result.model_dump_json() for result in results]
            self.work_log.data_storage.store_to_repo(
                REPO_EXTRACTED_DATA,
                "TEAM_RELEVANCY",
                {
                    "collapsed": "DONE",
                    "expanded": results_dict,
                    "summary": {
                        "total_teams": len(results),
                        "relevant_teams": sum(1 for r in results if r.is_relevant),
                        "not_relevant_teams": sum(
                            1 for r in results if not r.is_relevant
                        ),
                    },
                },
            )

            update_task_status(
                self.work_log,
                TaskKeys.COMPUTE_IMPACT_ON_EACH_TEAM,
                TaskStatus.COMPLETED,
            )
            return results

        except Exception as e:
            logger.error(f"Error during relevancy classification: {e}")
            update_task_status(
                self.work_log, TaskKeys.COMPUTE_IMPACT_ON_EACH_TEAM, TaskStatus.FAILED
            )
            raise RuntimeError(f"Relevancy classification failed: {e}") from e
