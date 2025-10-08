from pathlib import Path
from typing import Callable

from smolagents import CodeAgent, LiteLLMModel, Tool

from service.agent_core.constants import (
    REPO_AGENT_RESPONSE,
    REPO_INSIGHTS,
    REPO_PANDAS_OBJECTS,
    REPO_RESULTS,
)
from service.agent_core.data_management.data_documentation import DataDocumentation
from service.agent_core.explainability.explainability_service import (
    ExplainabilityService,
)
from service.agent_core.models import WorkLog
from service.agent_core.tools.branch_risk_tool import BranchRiskTool
from service.agent_core.tools.business_partner_priority_tool import (
    BusinessPartnerPriorityMatrixTool,
)
from service.agent_core.tools.business_partner_products_tool import (
    BusinessPartnerProductsTool,
)
from service.agent_core.tools.business_partner_risk_tool import BusinessPartnerRiskTool
from service.agent_core.tools.compare_branch_risks_tool import CompareBranchRisksTool
from service.agent_core.tools.data_analysis_agent_tool import DataAnalysisAgentTool
from service.agent_core.tools.find_branches_tool import FindBranchesTool
from service.agent_core.tools.find_category_or_product_tool import (
    FindCategoryOrProductTool,
)
from service.agent_core.tools.find_natural_resource_tool import (
    FindNaturalResourcesPerPartnerTool,
)
from service.agent_core.tools.find_partner_id_by_name_tool import (
    FindPartnerIdByNameTool,
)
from service.agent_core.tools.inspect_column_values_tool import InspectColumnValuesTool
from service.agent_core.tools.inspect_data_tool import InspectDataTool
from service.agent_core.tools.load_data_tool import LoadDataTool
from service.agent_core.tools.pandas_dataframe_tool import PandasDataFrameTool
from service.agent_core.tools.present_results_tool import PresentResultsTool
from service.agent_core.tools.products_by_country_tool import ProductsByCountryTool
from service.agent_core.tools.resource_risk_tool import ResourceRiskTool
from service.agent_core.tools.riskiest_resources_tool import (
    RiskiestResourcesOfBusinessPartnerTool,
)
from service.agent_core.tools.save_data_tool import SaveDataTool
from service.agent_core.tools.summarize_business_partner_tool import (
    SummarizeBusinessPartnersTool,
)
from service.data_preparation import (
    BUSINESS_PARTNERS_PARQUET,
    RESOURCE_RISKS_PROCESSED_PARQUET,
    RISK_PER_BRANCH_PARQUET,
    RISK_PER_BUSINESS_PARTNER_PARQUET,
    TRANSACTIONS_PARQUET,
)
from service.dependencies import with_settings
from service.settings import Settings

# Define the absolute path to the data directory relative to the service root
SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = SERVICE_ROOT / "data"

# Repository keys are now imported from constants module


data_analysis_tool_name = "data_analysis_agent_tool"

transaction_file = DATA_DIR / TRANSACTIONS_PARQUET


def initialize_tools(
    lite_llm_models: dict[str, LiteLLMModel],
    execution_id: str,
    work_log: WorkLog,
    settings: Settings,
) -> dict[str, Tool]:
    # stores raw data, as retrieved from the database
    work_log.data_storage.define_repo(REPO_PANDAS_OBJECTS)
    # stores data displayed during the query process, before the final result is displayed
    work_log.data_storage.define_repo(REPO_INSIGHTS)
    # stored final agent response, as returned by the Smolagent
    work_log.data_storage.define_repo(REPO_AGENT_RESPONSE)
    # stores final results/findings for the user, separately from pandas data
    work_log.data_storage.define_repo(REPO_RESULTS)

    pandas_dataframe_tool = PandasDataFrameTool(
        data_files=DataDocumentation.get_all_data_files_with_descriptions(),
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )
    summarize_business_partners_tool = SummarizeBusinessPartnersTool(
        business_partner_file=DATA_DIR / BUSINESS_PARTNERS_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    business_partner_risk_tool = BusinessPartnerRiskTool(
        risk_per_business_partner_file=DATA_DIR / RISK_PER_BUSINESS_PARTNER_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    business_partner_products_tool = BusinessPartnerProductsTool(
        transaction_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    riskiest_resources_tool = RiskiestResourcesOfBusinessPartnerTool(
        transaction_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    products_by_country_tool = ProductsByCountryTool(
        transaction_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    branch_risk_tool = BranchRiskTool(
        risk_per_branch_file=DATA_DIR / RISK_PER_BRANCH_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    compare_branch_risks_tool = CompareBranchRisksTool(
        risk_per_branch_file=DATA_DIR / RISK_PER_BRANCH_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    find_branches_tool = FindBranchesTool(
        risk_per_branch_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    present_results_tool = PresentResultsTool(
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_RESULTS,
    )

    find_partner_id_by_name_tool = FindPartnerIdByNameTool(
        business_partner_file=DATA_DIR / BUSINESS_PARTNERS_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    find_category_or_product_tool = FindCategoryOrProductTool(
        transaction_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    save_data_tool = SaveDataTool(
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_PANDAS_OBJECTS,
    )

    load_data_tool = LoadDataTool(
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_PANDAS_OBJECTS,
    )

    inspect_data_tool = InspectDataTool(
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_PANDAS_OBJECTS,
    )

    inspect_column_values_tool = InspectColumnValuesTool(
        data_files=DataDocumentation.get_all_data_files_with_descriptions(),
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
        repo_key=REPO_PANDAS_OBJECTS,
    )

    # Business partner priority matrix tool
    bp_priority_matrix_tool = BusinessPartnerPriorityMatrixTool(
        business_partner_file=DATA_DIR / BUSINESS_PARTNERS_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    resource_risk_tool = ResourceRiskTool(
        resource_risk_file=DATA_DIR / RESOURCE_RISKS_PROCESSED_PARQUET,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    find_natural_resource_tool = FindNaturalResourcesPerPartnerTool(
        transactions_file=transaction_file,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    data_analysis_tools: list[Tool] = [
        inspect_data_tool,
        save_data_tool,
        pandas_dataframe_tool,
        load_data_tool,
        inspect_column_values_tool,
        find_category_or_product_tool,
    ]

    data_analysis_agent_tool = DataAnalysisAgentTool(
        lite_llm_models=lite_llm_models,
        data_analysis_tools=data_analysis_tools,
        data_storage=work_log.data_storage,
        execution_id=execution_id,
        work_log=work_log,
    )

    return {
        "pandas_dataframe_tool": pandas_dataframe_tool,
        "summarize_business_partners": summarize_business_partners_tool,
        "business_partner_risk_tool": business_partner_risk_tool,
        "get_business_partner_products": business_partner_products_tool,
        "riskiest_resources_for_business_partner": riskiest_resources_tool,
        "get_products_by_country": products_by_country_tool,
        "branch_risk_tool": branch_risk_tool,
        "compare_branch_risks_tool": compare_branch_risks_tool,
        "find_branches_tool": find_branches_tool,
        "present_results": present_results_tool,
        "find_partner_id_by_name": find_partner_id_by_name_tool,
        "find_category_or_product": find_category_or_product_tool,
        "save_data": save_data_tool,
        "load_data": load_data_tool,
        "inspect_data": inspect_data_tool,
        "get_bp_prio_matrix_filtered": bp_priority_matrix_tool,
        "resource_risk_tool": resource_risk_tool,
        "find_natural_resource_per_partner": find_natural_resource_tool,
        data_analysis_tool_name: data_analysis_agent_tool,
    }


def initialize_agents(
    models: dict[str, LiteLLMModel],
    tools: dict[str, Tool],
    work_log: WorkLog,
    execution_id: str,
) -> dict[str, CodeAgent]:
    step_callbacks: list[Callable] = [
        ExplainabilityService.get_single_instance().make_callback(execution_id)
    ]

    query_agent_tools: list[Tool] = [
        tools["inspect_data"],
        tools["save_data"],
        tools["summarize_business_partners"],
        tools["business_partner_risk_tool"],
        tools["get_business_partner_products"],
        tools["riskiest_resources_for_business_partner"],
        tools["get_products_by_country"],
        tools["branch_risk_tool"],
        tools["compare_branch_risks_tool"],
        tools["find_branches_tool"],
        tools["present_results"],
        tools["find_partner_id_by_name"],
        tools["find_category_or_product"],
        tools["get_bp_prio_matrix_filtered"],
        tools["find_natural_resource_per_partner"],
        tools["resource_risk_tool"],
        tools["data_analysis_agent_tool"],
    ]

    settings = with_settings()
    query_agent = CodeAgent(
        model=models[settings.model_query_agent],
        tools=query_agent_tools,
        additional_authorized_imports=["pandas", "numpy"],
        max_steps=10,
        verbosity_level=2,
        planning_interval=None,
        name="query_agent",
        provide_run_summary=False,
        code_block_tags="markdown",
        step_callbacks=step_callbacks,
    )

    return {"query_agent": query_agent}
