import litellm
from loguru import logger
from smolagents import CodeAgent, LiteLLMModel, Tool

from service.agent_core.llm.aleph_alpha_llm_provider import AALLMProvider
from service.agent_core.models import WorkLog
from service.agent_core.tools.fix_xml_tool import FixXMLTool
from service.agent_core.tools.llm_completion_tool import LLMCompletionTool
from service.agent_core.tools.search_and_log_incidents_tool import (
    SearchAndExtractInsightsTool,
)
from service.agent_core.tools.visit_webpage_tool import VisitWebpageUserAgentTool
from service.agent_core.tools.xml_report_generator_tool import GenerateXMLReportTool
from service.dependencies import with_settings

# Repository keys for each tool
REPO_GOOGLE_SEARCH = "GOOGLE_SEARCH"
REPO_VISIT_WEBPAGE = "VISIT_WEBPAGE"
REPO_INSIGHTS = "INSIGHTS"
REPO_RESEARCH_RESULTS = "RESEARCH_RESULTS"


def initialize_model() -> LiteLLMModel:
    settings = with_settings()
    model_id = f"aleph-alpha/{settings.completion_model_name}"
    aa_llm_provider = AALLMProvider()
    litellm.custom_provider_map = [
        {"provider": "aleph-alpha", "custom_handler": aa_llm_provider}
    ]

    custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

    model = LiteLLMModel(
        model_id,
        custom_role_conversions=custom_role_conversions,
        max_completion_tokens=8192,
    )

    return model


def initialize_tools(
    lite_llm_model: LiteLLMModel, execution_id: str, work_log: WorkLog
) -> dict[str, Tool]:
    # Define repositories for each tool
    work_log.data_storage.define_repo(REPO_GOOGLE_SEARCH)
    work_log.data_storage.define_repo(REPO_VISIT_WEBPAGE)
    work_log.data_storage.define_repo(REPO_INSIGHTS)
    work_log.data_storage.define_repo(REPO_RESEARCH_RESULTS)

    logger.info(
        "Defined repositories: {}, {}, {}, {}",
        REPO_GOOGLE_SEARCH,
        REPO_VISIT_WEBPAGE,
        REPO_INSIGHTS,
        REPO_RESEARCH_RESULTS,
    )

    search_and_log_tool = SearchAndExtractInsightsTool(
        data_storage=work_log.data_storage,
        google_search_repo_key=REPO_GOOGLE_SEARCH,
        insights_repo_key=REPO_INSIGHTS,
        execution_id=execution_id,
        work_log=work_log,
        model=lite_llm_model,
        provider="serper",
    )
    visit_webpage_tool = VisitWebpageUserAgentTool(
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_VISIT_WEBPAGE,
    )
    llm_completion_tool = LLMCompletionTool(lite_llm_model, execution_id, work_log)
    fix_xml_tool = FixXMLTool(llm_completion_tool, work_log)
    xml_generator_tool = GenerateXMLReportTool(
        llm_completion_tool, fix_xml_tool, work_log
    )

    return {
        "search_and_log_tool": search_and_log_tool,
        "visit_webpage_tool": visit_webpage_tool,
        "log_tool": search_and_log_tool.log_tool,
        "llm_completion_tool": llm_completion_tool,
        "fix_xml_tool": fix_xml_tool,
        "xml_generator_tool": xml_generator_tool,
    }


def initialize_agents(
    model: LiteLLMModel, tools: dict[str, Tool], work_log: WorkLog
) -> dict[str, CodeAgent]:
    research_agent = CodeAgent(
        model=model,
        tools=[
            tools["search_and_log_tool"],
            tools["visit_webpage_tool"],
        ],
        additional_authorized_imports=["json"],
        max_steps=10,
        verbosity_level=2,
        planning_interval=None,
        name="google_search_agent",
        provide_run_summary=False,
    )

    return {"research_agent": research_agent}
