"""Integration tests for RelevancyClassifierFullText class."""

from typing import List

import pytest

from service.law_core.models import (
    FlowTask,
    TaskStatus,
    WorkLog,
)
from service.law_core.relevancy_classification.relevancy_classifier_full_text import (
    RelevancyClassifierFullText,
)
from service.law_core.summary.model_tools_manager import (
    REPO_EXTRACTED_DATA,
    initialize_model,
)
from service.law_core.summary.summary_work_log_manager import TaskKeys
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.models import (
    CompanyConfig,
    RelevancyClassifierLegalActInput,
    TeamDescription,
    TeamRelevancy,
)


@pytest.fixture
def sample_teams() -> List[TeamDescription]:
    """Create sample team descriptions for testing."""
    return [
        TeamDescription(
            name="Data Protection Team",
            description="Responsible for GDPR compliance and data privacy",
            department="Legal",
            daily_processes=["Data audit", "Privacy impact assessments"],
            relevant_laws_or_topics="GDPR, CCPA, data protection",
        ),
        TeamDescription(
            name="IT Security Team",
            description="Manages cybersecurity and IT infrastructure",
            department="IT",
            daily_processes=["Security monitoring", "Incident response"],
            relevant_laws_or_topics="Cybersecurity regulations, data breaches",
        ),
        TeamDescription(
            name="HR Team",
            description="Human resources and employee management",
            department="HR",
            daily_processes=["Employee onboarding", "Training coordination"],
            relevant_laws_or_topics="Employment law, workplace safety",
        ),
    ]


@pytest.fixture
def company_config(sample_teams: List[TeamDescription]) -> CompanyConfig:
    """Create a sample company configuration."""
    return CompanyConfig(
        company_description="A technology company focused on data analytics and AI solutions",
        teams=sample_teams,
    )


@pytest.fixture
def empty_company_config() -> CompanyConfig:
    return CompanyConfig(company_description="Example company", teams=[])


@pytest.fixture
def work_log() -> WorkLog:
    task = FlowTask(
        key=TaskKeys.COMPUTE_IMPACT_ON_EACH_TEAM.value,
        description="Computing impact on each team",
        status=TaskStatus.PENDING,
    )

    work_log = WorkLog(
        id="test-execution-id", status=TaskStatus.IN_PROGRESS, tasks=[task]
    )
    work_log.data_storage.define_repo(REPO_EXTRACTED_DATA)

    return work_log


@pytest.fixture
def sample_law_text() -> str:
    """Sample law text for testing."""
    return """
    Article 1: Scope and Definitions
    This regulation applies to all data processing activities within the European Union.

    Article 2: Data Controller Responsibilities
    Data controllers must implement appropriate technical and organizational measures.

    Article 3: Data Subject Rights
    Data subjects have the right to access, rectify, and erase their personal data.

    Article 4: Penalties and Sanctions
    Violations of this regulation may result in administrative fines up to 4% of annual turnover.
    """


@pytest.fixture
def sample_summary() -> str:
    return "This regulation governs all data processing activities within the European Union. It obliges data controllers to implement appropriate security measures while granting data subjects rights to access, rectify, and erase their personal data. Violations may lead to fines of up to 4% of an organization's annual turnover."


@pytest.fixture
def llm_completion_tool(work_log: WorkLog) -> LLMCompletionTool:
    """Mock LLMCompletionTool for testing."""
    return LLMCompletionTool(
        lite_llm_model=initialize_model(),
        execution_id="test-execution-id",
        work_log=work_log,
    )


class TestRelevancyClassifierFullLawTextAndLawTitle:
    """Integration tests for RelevancyClassifierFullText."""

    def test_init_creates_classifier_with_required_dependencies(
        self,
        work_log: WorkLog,
        company_config: CompanyConfig,
        llm_completion_tool: LLMCompletionTool,
    ) -> None:
        """Test that classifier initializes correctly with all dependencies."""
        classifier = RelevancyClassifierFullText(
            llm_completion_tool=llm_completion_tool,
            work_log=work_log,
            company_config=company_config,
            max_retries=3,
        )

        assert classifier.llm_completion_tool == llm_completion_tool
        assert classifier.work_log == work_log
        assert classifier.company_config == company_config
        assert classifier.max_retries == 3

    def test_classify_successful_classification_multiple_teams(
        self,
        work_log: WorkLog,
        company_config: CompanyConfig,
        sample_law_text: str,
        sample_summary: str,
        llm_completion_tool: LLMCompletionTool,
    ) -> None:
        """Test successful classification with multiple teams."""
        classifier = RelevancyClassifierFullText(
            llm_completion_tool=llm_completion_tool,
            work_log=work_log,
            company_config=company_config,
        )

        results = classifier.classify(
            RelevancyClassifierLegalActInput(
                title="foo",
                full_text=sample_law_text,
                url="http://does.not.matter",
                summary=sample_summary,
            )
        )

        # Verify results
        assert len(results) == len(company_config.teams)
        assert all(isinstance(result, TeamRelevancy) for result in results)

        team_names = {result.team_name for result in results}
        expected_teams = {"Data Protection Team", "IT Security Team", "HR Team"}
        assert team_names == expected_teams

        # Verify task status was updated
        task = work_log.get_single_task_with_key(
            TaskKeys.COMPUTE_IMPACT_ON_EACH_TEAM.value
        )
        assert task.status == TaskStatus.COMPLETED
