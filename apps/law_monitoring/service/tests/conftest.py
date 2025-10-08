from typing import List

import pytest

from service.law_core.models import FlowTask, TaskStatus, WorkLog
from service.law_core.summary.model_tools_manager import (
    REPO_EXTRACTED_DATA,
    initialize_model,
)
from service.law_core.summary.summary_work_log_manager import TaskKeys
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.models import CompanyConfig, TeamDescription


@pytest.fixture
def data_protection_team() -> TeamDescription:
    """Create sample team description for testing."""
    return TeamDescription(
        name="Data Protection Team",
        description="Responsible for GDPR compliance and data privacy",
        department="Legal",
        daily_processes=["Data audit", "Privacy impact assessments"],
        relevant_laws_or_topics="GDPR, CCPA, data protection",
    )


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
def llm_completion_tool(work_log: WorkLog) -> LLMCompletionTool:
    """Mock LLMCompletionTool for testing."""
    return LLMCompletionTool(
        lite_llm_model=initialize_model(),
        execution_id="test-execution-id",
        work_log=work_log,
    )


@pytest.fixture
def sample_summary() -> str:
    return "This regulation governs all data processing activities within the European Union. It obliges data controllers to implement appropriate security measures while granting data subjects rights to access, rectify, and erase their personal data. Violations may lead to fines of up to 4% of an organization's annual turnover."


@pytest.fixture
def company_config(sample_teams: List[TeamDescription]) -> CompanyConfig:
    """Create a sample company configuration."""
    return CompanyConfig(
        company_description="A technology company focused on data analytics and AI solutions",
        teams=sample_teams,
    )
